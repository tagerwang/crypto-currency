#!/usr/bin/env python3
"""
请求合并、缓存与限频池 - 多用户同机访问时降低币安 API 限频风险

核心功能：
1. 请求合并：并发相同请求只发起一次真实调用，其余等待并共享结果
2. 智能缓存：按 endpoint 配置不同 TTL（1s~60s），TTL 内直接返回缓存
3. 全局限频：60s 滑动窗口 + weight 累计，接近币安限制时自动等待到下一窗口

实现机制：
- 缓存键：api_type + endpoint + sorted(params)
- 线程安全：threading.Lock 保护共享状态
- 限频算法：weight_used + weight > 1200 时 sleep 等待窗口重置

配置参考：
- 所有 endpoint 的 TTL 和 weight 参考币安官方文档
- 1200 weight/min 限制（现货和合约通用）
"""

import json
import threading
import time
from typing import Dict, Any, Callable

# 全局限频配置（币安 API 限制：1200 weight/min）
RATE_LIMIT_WINDOW = 60.0  # 60 秒滑动窗口
MAX_WEIGHT_PER_MINUTE = 1200  # 每分钟最大权重

# 按 api_type + endpoint 配置 TTL（秒）和 weight（参考币安官方文档）
ENDPOINT_CONFIG = {
    "spot": {
        "/ticker/price": {"ttl": 1, "weight": 1},       # 单个 symbol weight=1
        "/ticker/24hr": {"ttl": 1, "weight": 1},        # 单个 symbol weight=1，所有 symbol weight=40
        "/klines": {"ttl": 5, "weight": 1},
        "/exchangeInfo": {"ttl": 60, "weight": 10},
        "/depth": {"ttl": 0.5, "weight": 5},            # 深度行情 weight=5
    },
    "futures": {
        "/ticker/price": {"ttl": 1, "weight": 1},
        "/ticker/24hr": {"ttl": 1, "weight": 1},        # 单个 symbol weight=1，所有 symbol weight=40
        "/klines": {"ttl": 5, "weight": 1},
        "/premiumIndex": {"ttl": 1, "weight": 1},       # 单个 symbol weight=1，所有 symbol weight=10
        "/fundingRate": {"ttl": 5, "weight": 1},
        "/openInterest": {"ttl": 5, "weight": 1},
        "/exchangeInfo": {"ttl": 60, "weight": 10},
        "/depth": {"ttl": 0.5, "weight": 5},
    },
    "futures_data": {
        "openInterestHist": {"ttl": 60, "weight": 1},
        "topLongShortAccountRatio": {"ttl": 60, "weight": 1},
        "topLongShortPositionRatio": {"ttl": 60, "weight": 1},
        "globalLongShortAccountRatio": {"ttl": 60, "weight": 1},
        "takerlongshortRatio": {"ttl": 60, "weight": 1},
    },
}

DEFAULT_CONFIG = {"ttl": 5, "weight": 1}


def _cache_key(api_type: str, endpoint: str, params: Dict) -> str:
    """生成稳定缓存键：api_type + endpoint + 排序后的 params JSON。"""
    params = params or {}
    params_str = json.dumps(params, sort_keys=True)
    return f"{api_type}:{endpoint}:{params_str}"


def _get_config(api_type: str, endpoint: str) -> Dict[str, Any]:
    """获取 endpoint 对应的配置（TTL 和 weight）。"""
    by_type = ENDPOINT_CONFIG.get(api_type, {})
    # 精确匹配
    if endpoint in by_type:
        return by_type[endpoint]
    # 前缀匹配（如 /ticker/24hr 无 params 时 endpoint 一致）
    for k, v in by_type.items():
        if endpoint.strip("/").startswith(k.strip("/")) or k in endpoint:
            return v
    return DEFAULT_CONFIG


class RequestPool:
    """
    请求合并、缓存与限频池（同步版）。
    - 相同 (api_type, endpoint, params) 的并发请求只发起一次真实请求，其余等待并共享结果。
    - 在 TTL 内的重复请求直接返回缓存，不再请求币安。
    - 全局限频：60s 滑动窗口，累计 weight 不超过 1200/min，超限时自动等待到下一个窗口。
    """

    __slots__ = ("_cache", "_pending", "_lock", "_weight_used", "_window_start")

    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._pending: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._weight_used = 0
        self._window_start = time.time()

    def _acquire_weight(self, weight: int) -> None:
        """
        在锁内获取权重配额，执行限频控制。
        如果当前窗口内权重已满，释放锁、等待到下一个窗口、重新获取锁并重置窗口。
        调用此方法时必须已持有 self._lock。
        """
        now = time.time()
        elapsed = now - self._window_start

        if elapsed >= RATE_LIMIT_WINDOW:
            # 窗口已过期，重置
            self._weight_used = 0
            self._window_start = now
        elif self._weight_used + weight > MAX_WEIGHT_PER_MINUTE:
            # 超限，释放锁并等待到下一个窗口
            wait_time = RATE_LIMIT_WINDOW - elapsed
            self._lock.release()
            time.sleep(wait_time)
            self._lock.acquire()
            # 重置窗口
            self._weight_used = 0
            self._window_start = time.time()

        # 累加权重
        self._weight_used += weight

    def fetch_with_dedup(
        self,
        api_type: str,
        endpoint: str,
        params: Dict,
        executor: Callable[[], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        带合并、缓存与限频的请求：先查缓存，再查是否已有进行中请求，否则执行 executor 并缓存。
        executor 为无参可调用对象，返回与 make_*_request 相同结构的 dict。
        """
        key = _cache_key(api_type, endpoint, params)
        config = _get_config(api_type, endpoint)
        ttl = config["ttl"]
        weight = config["weight"]
        now = time.time()

        with self._lock:
            # 1. 缓存命中
            entry = self._cache.get(key)
            if entry and (now - entry["timestamp"]) < ttl:
                return entry["data"]

            # 2. 已有进行中的请求：保存引用，退出 with 后等待，共享同一结果
            if key in self._pending:
                pend_ref = self._pending[key]
                ev = pend_ref["event"]
                break_wait = True
            else:
                break_wait = False

            # 3. 登记为进行中（仅当不是等待方时）
            if not break_wait:
                ev = threading.Event()
                self._pending[key] = {"event": ev, "result": None, "error": None}
                # 4. 获取权重配额（可能等待到下一个窗口）
                self._acquire_weight(weight)

        if break_wait:
            ev.wait()
            if pend_ref.get("error") is not None:
                raise pend_ref["error"]
            return pend_ref.get("result")

        result = None
        error = None
        try:
            result = executor()
            return result
        except Exception as e:
            error = e
            raise
        finally:
            with self._lock:
                pend = self._pending.get(key)
                if pend is not None:
                    if error is None and result is not None:
                        pend["result"] = result
                        self._cache[key] = {"data": result, "timestamp": time.time()}
                    else:
                        pend["error"] = error
                    pend["event"].set()
                    del self._pending[key]


# 全局单例，供 api 层使用
_request_pool = RequestPool()


def fetch_spot_with_dedup(endpoint: str, params: Dict, executor: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    return _request_pool.fetch_with_dedup("spot", endpoint, params or {}, executor)


def fetch_futures_with_dedup(endpoint: str, params: Dict, executor: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    return _request_pool.fetch_with_dedup("futures", endpoint, params or {}, executor)


def fetch_futures_data_with_dedup(endpoint: str, params: Dict, executor: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    return _request_pool.fetch_with_dedup("futures_data", endpoint, params or {}, executor)
