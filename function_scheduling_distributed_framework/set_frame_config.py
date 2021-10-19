# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2020/4/11 0011 0:56
"""

使用覆盖的方式，做配置。
"""
import copy
import sys
import time
import re
import importlib
from pathlib import Path
from shutil import copyfile
from nb_log import nb_print, stderr_write, stdout_write
from nb_log.monkey_print import is_main_process, only_print_on_main_process
from function_scheduling_distributed_framework import frame_config
import typing
from function_scheduling_distributed_framework.constant import BrokerEnum

if typing.TYPE_CHECKING:
    from typing import TypedDict


    class RedisConfigDict(TypedDict):
        host: str
        port: int
        password: str
        db: int


    class MongoConfigDict(TypedDict):
        host: typing.Union[str, typing.List[str]]
        username: str
        password: str
        db: str


    class RabbitmqConfigDict(TypedDict):
        host: str
        port: int
        user: str
        passwd: str
        vhost: str


    class KafkaConfigDict(TypedDict):
        bootstrap_servers: typing.List[str]


class FrameConfig:

    def set_base_config(self, **kwargs):
        for k, v in kwargs.items():
            setattr(frame_config, k, v)

    def set_mongo_config(self, mongo_config: 'MongoConfigDict', default_broker=True):
        host = mongo_config["host"]
        if type(host) is list:
            host = ','.join(mongo_config["host"])
        mongo_connect_url = f'mongodb://{mongo_config["username"]}:{mongo_config["password"]}@{host}/{mongo_config["db"]}'
        frame_config.MONGO_CONNECT_URL = mongo_connect_url
        if default_broker:
            frame_config.DEFAULT_BROKER_KIND = BrokerEnum.MONGOMQ

    def set_redis_config(self, redis_config: 'RedisConfigDict', default_broker=True):
        frame_config.REDIS_DB = redis_config['db']
        frame_config.REDIS_HOST = redis_config['host']
        frame_config.REDIS_PORT = redis_config['port']
        frame_config.REDIS_PASSWORD = redis_config['password']
        if default_broker:
            frame_config.DEFAULT_BROKER_KIND = BrokerEnum.REDIS_STREAM

    def set_kafka_config(self, kafka_config: 'KafkaConfigDict', default_broker=True):
        frame_config.KAFKA_BOOTSTRAP_SERVERS = kafka_config['bootstrap_servers']
        if default_broker:
            frame_config.DEFAULT_BROKER_KIND = BrokerEnum.KAFKA

    def set_rabbitmq_config(self, rabbitmq_config: 'RabbitmqConfigDict', default_broker=True):
        frame_config.RABBITMQ_HOST = rabbitmq_config['host']
        frame_config.RABBITMQ_PORT = rabbitmq_config['port']
        frame_config.RABBITMQ_USER = rabbitmq_config['user']
        frame_config.RABBITMQ_PASS = rabbitmq_config['passwd']
        frame_config.RABBITMQ_VIRTUAL_HOST = rabbitmq_config['vhost']
        if default_broker:
            frame_config.DEFAULT_BROKER_KIND = BrokerEnum.RABBITMQ_AMQPSTORM

    def set_default_logger(self, logger):
        self.logger = logger

# noinspection PyPep8Naming
# 这是手动调用函数设置配置，框架会自动调用use_config_form_distributed_frame_config_module读当前取项目根目录下的distributed_frame_config.py，不需要嗲用这里
def patch_frame_config(MONGO_CONNECT_URL: str = None,

                       RABBITMQ_USER: str = None,
                       RABBITMQ_PASS: str = None,
                       RABBITMQ_HOST: str = None,
                       RABBITMQ_PORT: int = None,
                       RABBITMQ_VIRTUAL_HOST: str = None,

                       REDIS_HOST: str = None,
                       REDIS_PASSWORD: str = None,
                       REDIS_PORT: int = None,
                       REDIS_DB: int = None,

                       NSQD_TCP_ADDRESSES: list = None,
                       NSQD_HTTP_CLIENT_HOST: str = None,
                       NSQD_HTTP_CLIENT_PORT: int = None,
                       KAFKA_BOOTSTRAP_SERVERS: list = None,

                       SQLACHEMY_ENGINE_URL='sqlite:////sqlachemy_queues/queues.db'

                       ):
    """
    对框架的配置使用猴子补丁的方式进行更改。利用了模块天然是单利的特性。格式参考frame_config.py
    :return:
    """
    kw = copy.copy(locals())
    for var_name, var_value in kw.items():
        if var_value is not None:
            setattr(frame_config, var_name, var_value)
    nb_print('使用patch_frame_config 函数设置框架配置了。')
    show_frame_config()


def show_frame_config():
    only_print_on_main_process('显示当前的项目中间件配置参数')
    for var_name in dir(frame_config):
        if var_name.isupper():
            var_value = getattr(frame_config, var_name)
            if var_name == 'MONGO_CONNECT_URL':
                if re.match('mongodb://.*?:.*?@.*?/.*', var_value):
                    mongo_pass = re.search('mongodb://.*?:(.*?)@', var_value).group(1)
                    mongo_pass_encryption = f'{"*" * (len(mongo_pass) - 2)}{mongo_pass[-1]}' if len(
                        mongo_pass) > 3 else mongo_pass
                    var_value_encryption = re.sub(r':(\w+)@', f':{mongo_pass_encryption}@', var_value)
                    only_print_on_main_process(f'{var_name}:             {var_value_encryption}')
                    continue
            if 'PASS' in var_name and var_value is not None and len(var_value) > 3:  # 对密码打*
                only_print_on_main_process(f'{var_name}:                {var_value[0]}{"*" * (len(var_value) - 2)}{var_value[-1]}')
            else:
                only_print_on_main_process(f'{var_name}:                {var_value}')


def use_config_form_distributed_frame_config_module():
    """
    自动读取配置。会优先读取启动脚本的目录的distributed_frame_config.py文件。没有则读取项目根目录下的distributed_frame_config.py
    :return:
    """
    return
    current_script_path = sys.path[0].replace('\\', '/')
    project_root_path = sys.path[1].replace('\\', '/')
    inspect_msg = f"""
    分布式函数调度框架会自动导入distributed_frame_config模块
    当第一次运行脚本时候，函数调度框架会在你的python当前项目的根目录下 {project_root_path} 下，创建一个名为 distributed_frame_config.py 的文件。
    自动读取配置，会优先读取启动脚本的所在目录 {current_script_path} 的distributed_frame_config.py文件，
    如果没有 {current_script_path}/distributed_frame_config.py 文件，则读取项目根目录 {project_root_path} 下的distributed_frame_config.py做配置。
    在 "{project_root_path}/distributed_frame_config.py:1" 文件中，需要按需重新设置要使用到的中间件的键和值，例如没有使用rabbitmq而是使用redis做中间件，则不需要配置rabbitmq。
    """
    # sys.stdout.write(f'\033[0;33m{time.strftime("%H:%M:%S")}\033[0m  "{__file__}:{sys._getframe().f_lineno}"   \033[0;30;43m{inspect_msg}\033[0m\n')
    # noinspection PyProtectedMember
    if is_main_process():
        stdout_write(f'\033[0;93m{time.strftime("%H:%M:%S")}\033[0m  "{__file__}:{sys._getframe().f_lineno}"   \033[0;93;100m{inspect_msg}\033[0m\n')
    try:
        # noinspection PyUnresolvedReferences
        # import distributed_frame_config
        m = importlib.import_module('distributed_frame_config')
        # nb_print(m.__dict__)
        only_print_on_main_process(f'分布式函数调度框架 读取到\n "{m.__file__}:1" 文件里面的变量作为优先配置了\n')
        for var_namex, var_valuex in m.__dict__.items():
            if var_namex.isupper():
                setattr(frame_config, var_namex, var_valuex)  # 用用户自定义的配置覆盖框架的默认配置。
    except ModuleNotFoundError:
        nb_print(
            f'''分布式函数调度框架检测到 你的项目根目录 {project_root_path} 和当前文件夹 {current_script_path}  下没有 distributed_frame_config.py 文件，\n\n''')
        auto_creat_config_file_to_project_root_path()

    show_frame_config()


def auto_creat_config_file_to_project_root_path():
    """
    在没有使用pycahrm运行代码时候，如果实在cmd 或者 linux 运行， python xx.py，
    请在临时会话窗口设置linux export PYTHONPATH=你的项目根目录 ，winwdos set PYTHONPATH=你的项目根目录
    :return:
    """
    # print(Path(sys.path[1]).as_posix())
    # print((Path(__file__).parent.parent).absolute().as_posix())
    # if Path(sys.path[1]).as_posix() in Path(__file__).parent.parent.absolute().as_posix():
    #     nb_print('不希望在本项目里面创建')
    #     return
    if '/lib/python' in sys.path[1] or r'\lib\python' in sys.path[1] or '.zip' in sys.path[1]:
        raise EnvironmentError(f'''如果是cmd 或者shell启动而不是pycharm 这种ide启动脚本，请先在会话窗口设置临时PYTHONPATH为你的项目路径，
                               windwos 使用 set PYTHONNPATH=你的当前python项目根目录,
                               linux 使用 export PYTHONPATH=你的当前你python项目根目录,
                               PYTHONPATH 作用是python的基本常识，请百度一下。
                               需要在会话窗口命令行设置临时的环境变量，而不是修改linux配置文件的方式设置永久环境变量，每个python项目的PYTHONPATH都要不一样，不要在配置文件写死''')
        return  # 当没设置pythonpath时候，也不要在 /lib/python36.zip这样的地方创建配置文件。

    file_name = Path(sys.path[1]) / Path('distributed_frame_config.py')
    copyfile(Path(__file__).absolute().parent / Path('frame_config.py'), file_name)
    nb_print(f'在  {Path(sys.path[1])} 目录下自动生成了一个文件， 请查看或修改 \n "{file_name}:1" 文件')
    # with (file_name).open(mode='w', encoding='utf8') as f:
    #     nb_print(f'在 {file_name} 目录下自动生成了一个文件， 请查看或修改 \n "{file_name}:1" 文件')
    #     f.write(config_file_content)

# use_config_form_distributed_frame_config_module()
