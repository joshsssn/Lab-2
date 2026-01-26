import configparser
import logging
import os
import pathlib
import sys

from app.utils.tools import listContains

logger = logging.getLogger(__name__)


DEFAULT_CONF = str(
    pathlib.Path(__file__).parent.parent.resolve() / "conf" / "config.ini"
)
print(DEFAULT_CONF)
DEFAULT_LOG_CONF = str(
    pathlib.Path(__file__).parent.parent.resolve() / "conf" / "logging.ini"
)
DEFAULT_LOG_PATH = pathlib.Path(__file__).parent.resolve() / "logs"
DEFAULT_DB_PATH = pathlib.Path(__file__).parent.resolve() / "db"
DEFAULT_DB_NAME = "database.db"
MANDATORY_SECTIONS = ["APP", "DATABASE"]
MANDATORY_KEYS = [
    "log_dir",
    "log_conf",
    "db_type",
    "path",
]
AVA_DB_TYPE = ["sqlite", "mysql", "postgresql", "mongodb"]
DEFAULT_DB_TYPE = "sqlite"


class ConfigManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(DEFAULT_CONF)
        self._valid()

    def _valid(self) -> None:
        """
        This function checks if the config file has a valid format or not. It must contain [APP],
        [DATABASE] section and keys such as LOG_DIR, DB_TYPE, ETC. If the config file does not
        contain the necessary information for launching the app. We consider this is a fatal error, and
        we stopped the program
        :return:
        """

        # check if the config has all mandatory sections
        if not listContains(MANDATORY_SECTIONS, self.config.sections()):
            logger.error(
                f"The configuration file is not valid, it misses mandatory sections: {MANDATORY_SECTIONS}"
            )
            sys.exit(1)
        allKeys = []
        # loop through all mandatory section and get all keys for each section
        for section in MANDATORY_SECTIONS:
            for key in dict(self.config.items(section)).keys():
                allKeys.append(key)
        # check if the config file has all mandatory keys
        if not listContains(MANDATORY_KEYS, allKeys):
            logger.error(
                f"The configuration file is not valid, it misses mandatory keys: {MANDATORY_KEYS}"
            )
            sys.exit(1)

    def showAllConfig(self) -> None:
        """
        This function prints all available conf field in the std out
        :return:
        """
        for section in self.config.sections():
            print(section)
            for key in self.config[section]:
                print((key, self.config[section][key]))

    def getLogOutputDir(self) -> str:
        """This function returns the log file dir where all logs will be stored. If the given config file path is
        empty or invalid, a default value will be returned
        """
        # no need to use try here, the _valid method check the existence of the section and key.
        res = self.config["APP"]["LOG_DIR"]
        # if the key is empty or not valid, use default value (and create the folder for default path)
        if res == "" or not os.path.exists(res):
            res = DEFAULT_LOG_PATH
            res.mkdir(parents=True, exist_ok=True)
            logger.warning(
                f"The provided log output dir path in the conf file is not valid, use default value {res}"
            )
        return str(res)

    def getLogConfPath(self) -> str:
        """This method returns the logger config file path, if empty, the default config file will
        be used

        :return: The path of the logger config file
        """
        res = self.config["APP"]["LOG_CONF"]
        if res == "" or not os.path.exists(res):
            res = DEFAULT_LOG_CONF
            logger.warning(
                f"The provided log config file path is not valid, use default value {res}"
            )
        return res

    def getDBType(self) -> str:
        res = self.config["DATABASE"]["DB_TYPE"]
        # The given db type
        if res == "" or not (res in AVA_DB_TYPE):
            res = DEFAULT_DB_TYPE
            logger.warning(
                f"The provided log config file path is not valid, use default value {res}"
            )
        return res

    def getDBUrl(self) -> str:
        dbType = self.getDBType()
        if dbType == "sqlite":
            res = self.config["DATABASE"]["PATH"]
            # if the database path is empty or not valid, use default value
            if res == "" or not os.path.exists(res):
                DEFAULT_DB_PATH.mkdir(parents=True, exist_ok=True)
                res = f"{str(DEFAULT_DB_PATH)}/{DEFAULT_DB_NAME}"
            return res

        elif dbType == "mongodb":
            # MongoDB connection string: mongodb://user:password@host:port/database
            # MongoDB connection string: mongodb://user:password@host:port/database
            user = os.getenv("DB_USER", self.config["DATABASE"]["USERNAME"])
            password = os.getenv("DB_PASSWORD", self.config["DATABASE"]["PASSWORD"])
            host = os.getenv("DB_HOST", self.config["DATABASE"]["HOST"])
            port = os.getenv("DB_PORT", self.config["DATABASE"]["PORT"])
            db_name = os.getenv("DB_NAME", self.config["DATABASE"]["DB"])
            
            return "mongodb://{}:{}@{}:{}/{}?authSource=admin".format(
                user, password, host, port, db_name
            )

        # This is what you need to add in the conf if you want to replace sqlite with postgre or mysql ! that's all
        else:
            return "{}:{}@{}:{}/{}".format(
                self.config["DATABASE"]["USERNAME"],
                self.config["DATABASE"]["PASSWORD"],
                self.config["DATABASE"]["HOST"],
                self.config["DATABASE"]["PORT"],
                self.config["DATABASE"]["DB"],
            )

    def getMongoDBName(self) -> str:
        """Returns the MongoDB database name."""
        return self.config["DATABASE"]["DB"]
