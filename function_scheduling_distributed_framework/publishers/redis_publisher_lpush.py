# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12
from function_scheduling_distributed_framework.constant import BrokerEnum
from function_scheduling_distributed_framework.publishers.redis_publisher import RedisPublisher


class RedisPublisherLpush(RedisPublisher):
    BROKER_KIND = BrokerEnum.REDIS_DOUBLE_LIST
    """
    使用redis作为中间件,
    """

    _push_method = 'lpush'


