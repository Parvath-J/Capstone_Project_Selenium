import configparser

config = configparser.RawConfigParser()
config.read('./configurations/config.ini')


class ReadConfig:
    @staticmethod
    def getApplicationURL():
        url = config.get('common info', 'baseURL')
        return url

    @staticmethod
    def getUsername():
        username = config.get('common info', 'username')
        return username

    @staticmethod
    def getPassword():
        password = config.get('common info', 'password')
        return password

    # --- ADD THESE NEW METHODS ---
    @staticmethod
    def getInternetHerokuappURL():
        url = config.get('common info', 'internet_herokuapp_url')
        return url

    @staticmethod
    def getDemoQAURL():
        url = config.get('common info', 'demoqa_url')
        return url