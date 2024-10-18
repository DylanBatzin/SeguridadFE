def validar_dpi(dpi):

    if len(dpi) != 13 or not dpi.isdigit():
        return False

  
    numeros_dpi = [int(d) for d in dpi[:12]]
    digito_verificador = int(dpi[12])

 
    pesos = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]


    suma = sum(n * p for n, p in zip(numeros_dpi, pesos))


    residuo = suma % 11

 
    digito_calculado = 11 - residuo


    if digito_calculado == 11:
        digito_calculado = 0

    return digito_calculado == digito_verificador

