class Car:
    def __init__(self, brand):
        # self.brand = brand
        self.__brand = brand

    @property
    def brand(self):
        #return self.brand
        return self.__brand
    # def set_brand(self, brand):
    #     self.brand = brand
    @brand.setter
    def brand(self, brand):
        #self.brand = brand
        self.__brand = brand
    # def get_brand(self):
    #     return self.brand
    

if __name__ == '__main__':
    car = Car('차')
    # print(car.get_brand())
    print(car.brand)
    # car.set_brand('현대')
    # print(car.get_brand())
    car.brand = '현대'
    print(car.brand)
