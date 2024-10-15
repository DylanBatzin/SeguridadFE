def validar_dpi(dpi):
    # Asegurarse de que el DPI tenga exactamente 13 dígitos y sea numérico
    if len(dpi) != 13 or not dpi.isdigit():
        return False

    # Separar los primeros 12 dígitos y el dígito verificador
    numeros_dpi = [int(d) for d in dpi[:12]]
    digito_verificador = int(dpi[12])

    # Pesos para cada posición (del 2 al 13 de derecha a izquierda)
    pesos = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

    # Multiplicar cada dígito por su peso correspondiente
    suma = sum(n * p for n, p in zip(numeros_dpi, pesos))

    # Calcular el residuo de la división entre 11
    residuo = suma % 11

    # Calcular el dígito de verificación esperado
    digito_calculado = 11 - residuo

    # Si el resultado es 10 o 11, el DPI es inválido
    if digito_calculado == 11:
        digito_calculado = 0

    # Comparar el dígito calculado con el dígito verificador del DPI
    return digito_calculado == digito_verificador

# Ejemplo de uso:
dpi = "1704711790407"  # Sustituir por un DPI real
if validar_dpi(dpi):
    print("El DPI es válido.")
else:
    print("El DPI es inválido.")
