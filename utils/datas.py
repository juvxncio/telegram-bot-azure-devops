import calendar
from datetime import datetime, timedelta
import holidays


def calcular_horas_uteis(mes, ano):
    feriados = holidays.Brazil(years=ano, prov='SP')

    primeiro = datetime(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    ultimo = datetime(ano, mes, ultimo_dia)

    horas = 0
    dia = primeiro

    while dia <= ultimo:
        if dia.weekday() < 5 and dia not in feriados:
            if (
                dia.weekday() == 2
                and (dia - timedelta(days=1)) in feriados
                and 'Carnaval' in feriados.get(dia - timedelta(days=1), '')
            ):
                horas += 4
            else:
                horas += 8
        dia += timedelta(days=1)

    return horas
