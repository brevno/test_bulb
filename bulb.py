# -*- coding: utf-8 -*-
class Bulb(object):
    def __init__(self):
        self.is_on = False
        self.color = ''

    def set_power_state(self, new_status):
        if new_status in ['on', 'ON']:
            self.is_on = True

            # Если лампочку только что включили, по умолчанию она будет белого цвета
            if self.color == '':
                self.color = 'white'

        elif new_status in ['off', 'OFF']:
            self.is_on = False

    def set_color(self, color):
        self.color = color

    def get_data(self):
        return {'status': self.is_on, 'color': self.color}

    def as_dict(self):
        return self.get_data()
