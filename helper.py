import configparser


# Method to read config file settings
def read_config(config_file):
    config_obj = configparser.ConfigParser()
    # with open('config.ini', 'r') as file:
    #     config = file.read()
    config_obj.read(config_file)
    return config_obj


def save_config(config_file, config_obj, section, field, value):

    config_obj[section][field] = value
    with open(config_file, "w") as file_obj:
        config_obj.write(file_obj)

    return
