# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 14:57
import time
from function_scheduling_distributed_framework.constant import BrokerEnum
from function_scheduling_distributed_framework import get_publisher

pb = get_publisher('task1_queue', broker_kind=BrokerEnum.REDIS_LIST)

for i in range(100):
    pb.publish({'x': i, 'y': i * 2})
