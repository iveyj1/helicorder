import configparser
def getconfig(config_file_name):
    config = configparser.ConfigParser()
    try:
        with open(config_file_name, 'r') as configfile:
            config.read_file(configfile)
    except IOError:
        config["DEFAULT"] = {
                                'com_port' : '/dev/ttyUSB0', 
                                'baud_rate' : '9600', 
                                'out_file_base_name' : "seismo_", 
                                'server_port' : '5067', 
                                'get_quakes':'False',
                                'quake_url':'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson',
                                'sample_rate':10

                            }

        config["MONITOR"] = {
                                'trace_duration':900,
                                'display_y_offset':'0',
                                'display_y_max':100000,
                                'display_y_min':-100000,
                                'update_delay':250,
                                'server_address' : '127.0.0.1'
        }

        with open(config_file_name, 'w') as configfile:
            print('configuration file not found - default {} written'.format(config_file_name))
            config.write(configfile)
    return config
