from mysql_python_module.MySQL.DBParams import DBParams
from mysql_python_module.MySQL.MySqlAdaptor import MySqlAdaptor
from mysql_python_module.MySQL.MySqlDBConnection import MySqlDBConnection
import configSetting


class RPABaseAdaptor(MySqlAdaptor):
    def __init__(self):
        db_params = DBParams(host=configSetting.RPA_HOST,
                             port=configSetting.RPA_PORT,
                             user=configSetting.RPA_USER,
                             password=configSetting.RPA_PWD,
                             db=configSetting.RPA_DB,
                             timeout=configSetting.RPA_TIMEOUT,
                             charset='utf8mb4', )
        super(RPABaseAdaptor, self).__init__(MySqlDBConnection(db_params))
