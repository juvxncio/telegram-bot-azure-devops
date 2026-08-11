from datetime import datetime

from bot import handlers


def test_calcula_mes_ano_padrao_sem_args_retorna_mes_anterior(monkeypatch):
    class DatetimeFixo(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 11)

    monkeypatch.setattr(handlers, 'datetime', DatetimeFixo)

    assert handlers.calcula_mes_ano_padrao([]) == (7, 2026)


def test_calcula_mes_ano_padrao_em_janeiro_volta_para_dezembro_anterior(monkeypatch):
    class DatetimeFixo(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 1, 15)

    monkeypatch.setattr(handlers, 'datetime', DatetimeFixo)

    assert handlers.calcula_mes_ano_padrao([]) == (12, 2025)


def test_calcula_mes_ano_padrao_com_mes_e_ano_explicitos():
    assert handlers.calcula_mes_ano_padrao(['5', '2024']) == (5, 2024)


def test_calcula_mes_ano_padrao_so_com_mes_usa_ano_atual(monkeypatch):
    class DatetimeFixo(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 8, 11)

    monkeypatch.setattr(handlers, 'datetime', DatetimeFixo)

    assert handlers.calcula_mes_ano_padrao(['3']) == (3, 2026)


def test_chat_autorizado_aceita_o_grupo_configurado():
    assert handlers.chat_autorizado(handlers.GRUPO_PERMITIDO) is True


def test_chat_autorizado_rejeita_outro_chat():
    assert handlers.chat_autorizado(handlers.GRUPO_PERMITIDO + 1) is False


def test_obter_relatorios_reaproveita_a_mesma_instancia():
    r1 = handlers.obter_relatorios()
    r2 = handlers.obter_relatorios()
    assert r1 is r2
