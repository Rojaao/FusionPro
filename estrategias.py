
def estrategia_6em7digit(digitos):
    return sum(1 for d in digitos[-7:] if d <= 3) >= 6

def estrategia_0matador(digitos):
    return all(d >= 4 for d in digitos[-8:])

def estrategia_4acima(digitos):
    return sum(1 for d in digitos[-8:] if d >= 4) >= 6
