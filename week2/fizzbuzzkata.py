def FizzBuzz():

    num = input('What is your number')

    if ((int(num) % 3 ==0) & (int(num) % 5 == 0)) :
        print('FizzBuzz')
    elif int(num) % 3 == 0 :
        print('Fizz')
    elif int(num) % 5 == 0:
        print('Buzz')
    else :
        print(num)

FizzBuzz()