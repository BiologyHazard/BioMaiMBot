import os
import shutil
import sys
from pathlib import Path

import nonebot
from dotenv import load_dotenv
from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter
from nonebot.log import default_filter, logger

logger_format: str = (
    '<dim>File <cyan>"{file.path}"</>, line <cyan>{line}</>, in <cyan>{function}</></>'
    "\n"
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> "
    "[<level>{level}</>] "
    # "<cyan><underline>{name}</></>:"
    # "<cyan>{function}</>:<cyan>{line}</> | "
    "<level><normal>{message}</></>"
)
logger.remove()
logger.add(sys.stderr,
           level=0,
           format=logger_format,
           filter=default_filter)
logger.add('logs/bot_{time:YYYY-MM-DD}.log',
           level=0,
           rotation='00:00',
           format=logger_format,
           filter=default_filter)

# 初次启动检测
if not Path("config/bot_config.toml").exists() or not Path(".env").exists():
    logger.info("检测到bot_config.toml不存在，正在从模板复制")
    shutil.copy(Path("config/bot_config_template.toml"), Path("config/bot_config.toml"))
    logger.info("复制完成，请修改config/bot_config.toml和.env.prod中的配置后重新启动")

# 初始化.env 默认ENVIRONMENT=prod
if not Path(".env").exists():
    with open(Path(".env"), "w") as f:
        f.write("ENVIRONMENT=prod")

    # 检测.env.prod文件是否存在
    if not Path(".env.prod").exists():
        logger.error("检测到.env.prod文件不存在")
        shutil.copy(Path("template.env"), Path(".env.prod"))

# 首先加载基础环境变量.env
if Path(".env").exists():
    load_dotenv(Path(".env"))
    logger.success("成功加载基础环境变量配置")

# 根据 ENVIRONMENT 加载对应的环境配置
if os.getenv("ENVIRONMENT") == "prod":
    logger.success("加载生产环境变量配置")
    load_dotenv(Path(".env.prod"), override=True)  # override=True 允许覆盖已存在的环境变量
elif os.getenv("ENVIRONMENT") == "dev":
    logger.success("加载开发环境变量配置")
    load_dotenv(Path(".env.dev"), override=True)  # override=True 允许覆盖已存在的环境变量
elif Path(f".env.{os.getenv('ENVIRONMENT')}").exists():
    logger.success(f"加载{os.getenv('ENVIRONMENT')}环境变量配置")
    load_dotenv(Path(f".env.{os.getenv('ENVIRONMENT')}"), override=True)  # override=True 允许覆盖已存在的环境变量
else:
    logger.error(f"ENVIRONMENT配置错误，请检查.env文件中的ENVIRONMENT变量对应的.env.{os.getenv('ENVIRONMENT')}是否存在")
    exit(1)

# 检测Key是否存在
if not os.getenv("SILICONFLOW_KEY"):
    logger.error("缺失必要的API KEY")
    logger.error(f"请至少在.env.{os.getenv('ENVIRONMENT')}文件中填写SILICONFLOW_KEY后重新启动")
    exit(1)

# 获取所有环境变量
env_config = {key: os.getenv(key) for key in os.environ}

# 设置基础配置
base_config = {
    "websocket_port": int(env_config.get("PORT", 8080)),
    "host": env_config.get("HOST", "127.0.0.1"),
    "log_level": "INFO",
}

# 合并配置
nonebot.init(**base_config, **env_config)

# 注册适配器
driver = nonebot.get_driver()
driver.register_adapter(OnebotV11Adapter)

# 加载插件
nonebot.load_plugins("src/plugins")

if __name__ == "__main__":
    nonebot.run()
