import calendar
from datetime import date, datetime, timedelta

from utils.datas import calcular_horas_uteis


def _dias_uteis_no_mes(mes, ano):
    total_dias = calendar.monthrange(ano, mes)[1]
    return sum(
        1
        for dia in range(1, total_dias + 1)
        if date(ano, mes, dia).weekday() < 5
    )


def test_calcula_horas_uteis_sem_feriados(monkeypatch):
    monkeypatch.setattr('utils.datas.holidays.Brazil', lambda **kwargs: {})

    mes, ano = 9, 2025
    esperado = _dias_uteis_no_mes(mes, ano) * 8

    assert calcular_horas_uteis(mes, ano) == esperado


def test_feriado_em_dia_util_reduz_8_horas(monkeypatch):
    mes, ano = 9, 2025
    segunda = next(
        datetime(ano, mes, dia)
        for dia in range(1, calendar.monthrange(ano, mes)[1] + 1)
        if date(ano, mes, dia).weekday() == 0
    )

    monkeypatch.setattr('utils.datas.holidays.Brazil', lambda **kwargs: {})
    horas_sem_feriado = calcular_horas_uteis(mes, ano)

    monkeypatch.setattr(
        'utils.datas.holidays.Brazil',
        lambda **kwargs: {segunda: 'Feriado de teste'},
    )
    horas_com_feriado = calcular_horas_uteis(mes, ano)

    assert horas_sem_feriado - horas_com_feriado == 8


def test_quarta_feira_apos_carnaval_conta_4_horas_em_vez_de_8(monkeypatch):
    # Compara dois feriados na terça anterior à quarta: um chamado
    # "Carnaval" e outro não, isolando o efeito do meio-expediente na
    # quarta-feira (o dia da terça já sai do cálculo nos dois cenários).
    mes, ano = 9, 2025
    quarta = next(
        datetime(ano, mes, dia)
        for dia in range(1, calendar.monthrange(ano, mes)[1] + 1)
        if date(ano, mes, dia).weekday() == 2
    )
    terca_anterior = quarta - timedelta(days=1)

    monkeypatch.setattr(
        'utils.datas.holidays.Brazil',
        lambda **kwargs: {terca_anterior: 'Outro Feriado'},
    )
    horas_feriado_comum = calcular_horas_uteis(mes, ano)

    monkeypatch.setattr(
        'utils.datas.holidays.Brazil',
        lambda **kwargs: {terca_anterior: 'Carnaval'},
    )
    horas_com_carnaval = calcular_horas_uteis(mes, ano)

    assert horas_feriado_comum - horas_com_carnaval == 4
