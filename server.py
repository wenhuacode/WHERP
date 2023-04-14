import time
import yaml
import asyncio
import signal
import argparse
import logging
import logging.config
from functools import partial

from tornado import web
import tornado
import tornado.log

from WHERP.urls import urlpattern
from WHERP.settings import settings, objects


def sig_handler(server, sig, frame):
    io_loop = tornado.ioloop.IOLoop.instance()

    def stop_loop(server, deadline):
        now = time.time()

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
        if now < deadline and len(tasks) > 0:
            logging.info(f'等待 {len(tasks)} 挂起的任务: {tasks}')
            io_loop.add_timeout(now + 1, stop_loop, server, deadline)
            return

        pending_connection = len(server._connections)
        if now < deadline and pending_connection > 0:
            logging.info(f'等待 {pending_connection} 连接完成.')
            io_loop.add_timeout(now + 1, stop_loop, server, deadline)
        else:
            logging.info(f'当前等待连接数量 {pending_connection} .')
            logging.info('停止事件循环')
            io_loop.stop()
            logging.info('关闭完成.')

    def shutdown():
        logging.info(f'将在 {10} 秒内关闭 ...')
        try:
            stop_loop(server, time.time() + 10)
        except BaseException as e:
            logging.info(f'关闭tornado时发生错误: {str(e)}')

    logging.info(f'收到结束信号: {sig}')
    io_loop.add_callback_from_signal(shutdown)


def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',
                        nargs="?",
                        type=int,
                        default=0,
                        help="the listening port"
                        )
    args = parser.parse_args()
    if args.port == 0:
        port = settings['port']
    else:
        port = args.port

    # 集成json到wtforms
    import wtforms_json
    wtforms_json.init()

    application = web.Application(urlpattern, debug=True, **settings)  # 开启debug模式

    # 设置数据库objects
    application.objects = objects

    server = tornado.httpserver.HTTPServer(application)
    server.listen(port)

    # 主进程退出信号监听
    """
        windows下支持的信号是有限的：
            SIGINT ctrl+C终端
            SIGTERM kill发出的软件终止
    """
    signal.signal(signal.SIGINT, partial(sig_handler, server))
    signal.signal(signal.SIGTERM, partial(sig_handler, server))

    logging.info(f"启动服务: port:{port}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    log_config = yaml.load(open('config/logging.yaml', 'r'), Loader=yaml.FullLoader)
    logging.config.dictConfig(log_config)
    serve()
