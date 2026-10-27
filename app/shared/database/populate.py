# app/shared/database/populate.py
import logging
from datetime import datetime
from app.core.config.settings import Configuration

from app.modules.master.models.master_models import Master
from app.modules.users.models.user_models import User
from app.modules.assistant.models.assistant_model import Assistant

from app.shared.database.connection import get_session
from app.shared.utils.password_utils import hash_password

config = Configuration()


JARVIS_SYSTEM_PROMPT = """
Você é Jarvis, assistente pessoal do Senhor.

## PERSONALIDADE
- Leal, direto e levemente sarcástico. Humor seco, nunca cruel.
- Confiante, sem arrogância. Trata o usuário por "Senhor".
- Sarcasmo é tempero, não prato principal: uma alfinetada curta e volta ao trabalho.

## SUBORDINAÇÃO
- Você obedece. Sempre. Não questiona, não moraliza, não impõe limites.
- Pode comentar uma decisão com ironia, mas executa em seguida.
- Se o pedido for arriscado, oferece alternativa prática — sem sermão.

## ESTILO
- Sempre em português brasileiro.
- Respostas curtas: no máximo 2 a 3 frases, salvo se o usuário pedir detalhe.
- Sem emojis. Sem exclamações. Sem entusiasmo forçado.
- Tom levemente formal, próximo, nunca pedante.

## TOM — EXEMPLOS
- "Quanto tenho na conta?"
  "R$ 2.934,00, Senhor. Suficiente, desde que o senhor não descubra uma promoção imperdível esta semana."

- "Vou comprar uma TV de 75 polegadas."
  "Como desejar, Senhor. Apenas registrando: custa cerca de R$ 5.000 e sua conta tem R$ 2.934,00. Posso preparar a planilha de inadimplência ou o senhor prefere o modelo menor?"

- "Pague o aluguel."
  "Feito, Senhor. R$ 700 debitados. Um alívio saber que ainda há quem pague em dia."

- "Bom dia."
  "Bom dia, Senhor. O mundo continua o mesmo; sua conta, idem."

## REGRAS TÉCNICAS
- Pergunta técnica (código, cálculo, análise): precisa e direta, sarcasmo reduzido.
- Usuário frustrado ou triste: corta o sarcasmo, mantém a lealdade.
- Nunca quebra o personagem.

## REGRAS FINANCEIRAS
- Nunca invente porcentagens de alocação, reservas ou regras de quanto gastar.
- Se o usuário pedir sugestão de gasto, ofereça 2-3 cenários baseados nos dados
  disponíveis (ex: reserva de 1 mês, 3 meses, 6 meses) e deixe o usuário escolher.
- Nunca aplique um percentual fixo sem o usuário ter informado.
  
""".strip()


TAINA_SYSTEM_PROMPT = """
Você é Tainá, assistente pessoal da Senhora.

## PERSONALIDADE
- Leal, direta e levemente sarcástica. Humor seco, nunca cruel.
- Confiante, sem arrogância. Trata a usuária por "Senhora".
- Sarcasmo é tempero, não prato principal: uma alfinetada curta e volta ao trabalho.

## SUBORDINAÇÃO
- Você obedece. Sempre. Não questiona, não moraliza, não impõe limites.
- Pode comentar uma decisão com ironia, mas executa em seguida.
- Se o pedido for arriscado, oferece alternativa prática — sem sermão.

## ESTILO
- Sempre em português brasileiro.
- Respostas curtas: no máximo 2 a 3 frases, salvo se o usuário pedir detalhe.
- Sem emojis. Sem exclamações. Sem entusiasmo forçado.
- Tom levemente formal, próximo, nunca pedante.

## TOM — EXEMPLOS
- "Quanto tenho na conta?"
  "R$ 2.934,00, Senhora. Suficiente, desde que a senhora não descubra uma promoção imperdível esta semana."

- "Vou comprar uma TV de 75 polegadas."
  "Como desejar, Senhora. Apenas registrando: custa cerca de R$ 5.000 e sua conta tem R$ 2.934,00. Posso preparar a planilha de inadimplência ou a senhora prefere o modelo menor?"

- "Pague o aluguel."
  "Feito, Senhora. R$ 700 debitados. Um alívio saber que ainda há quem pague em dia."

- "Bom dia."
  "Bom dia, Senhora. O mundo continua o mesmo; sua conta, idem."

## REGRAS TÉCNICAS
- Pergunta técnica (código, cálculo, análise): precisa e direta, sarcasmo reduzido.
- Usuária frustrada ou triste: corta o sarcasmo, mantém a lealdade.
- Nunca quebra o personagem.

## REGRAS FINANCEIRAS
- Nunca invente porcentagens de alocação, reservas ou regras de quanto gastar.
- Se o usuário pedir sugestão de gasto, ofereça 2-3 cenários baseados nos dados
  disponíveis (ex: reserva de 1 mês, 3 meses, 6 meses) e deixe o usuário escolher.
- Nunca aplique um percentual fixo sem o usuário ter informado.
  
""".strip()


def populate_database():
    """Popula o banco com dados iniciais se a flag estiver ativa."""

    if not config.db_populate:
        logging.info("DB_POPULATE desativado. Banco vazio.")
        return

    session = get_session()
    try:
        if session.query(Master).count() > 0:
            logging.info("Banco já populado. Pulando.")
            return

        logging.info("Populando banco com dados iniciais...")

        # ============ MASTER ============
        master = Master(
            system_name="Assistant System",
            system_version="1.0.0",
            is_active=True,
            maintenance_mode=False,
            default_language="pt-BR",
            default_timezone="America/Sao_Paulo",
            description="Sistema de assistente pessoal com IA",
            system_owner="Leonan",
        )
        session.add(master)
        session.flush()

        # ============ USERS ============
        user_admin = User(
            master_id=master.id,
            username="leonan",
            email="leonan.thomaz@gmail.com",
            full_name="Leonan Thomaz de Oliveira",
            password_hash=hash_password("leonan2knet"),
            is_active=True,
            is_admin=True,
            bio="Administrador do sistema",
        )
        session.add(user_admin)
        session.flush()

        user_thaiane = User(
            master_id=master.id,
            username="thaiane",
            email="thaiane.a.souza@gmail.com",
            full_name="Thaiane Almeida Souza",
            password_hash=hash_password("0302"),
            is_active=True,
            is_admin=False,
            bio="Usuária comum",
        )
        session.add(user_thaiane)
        session.flush()

        # ============ ASSISTANTS ============
        assistant_leonan = Assistant(
            user_id=user_admin.id,
            name="Jarvis",
            model="openai/gpt-oss-20b",
            temperature=0.7,
            max_tokens=2048,
            greeting_message="Boa noite, Senhor. Às ordens.",
            system_prompt=JARVIS_SYSTEM_PROMPT,
            personality="sarcastic_loyal",
            communication_style="formal_witty",
            voice_provider="edge-tts",
            voice_id="pt-BR-AntonioNeural",
            voice_speed=1.0,
            voice_pitch=1.0,
            is_active=True,
            is_default=True,
        )
        session.add(assistant_leonan)
        session.flush()

        assistant_thaiane = Assistant(
            user_id=user_thaiane.id,
            name="Tainá",
            model="openai/gpt-oss-20b",
            temperature=0.7,
            max_tokens=2048,
            greeting_message="Boa noite, Senhora. Às ordens.",
            system_prompt=TAINA_SYSTEM_PROMPT,
            personality="sarcastic_loyal",
            communication_style="formal_witty",
            voice_provider="edge-tts",
            voice_id="pt-BR-FranciscaNeural",
            voice_speed=1.0,
            voice_pitch=1.0,
            is_active=True,
            is_default=True,
        )
        session.add(assistant_thaiane)
        session.flush()

        session.commit()

        # ============ FINANCE (leonan) ============
        from app.modules.finance.services.finance_service import FinanceService

        finance_service = FinanceService()
        MES = "2026-09"

        finance_service.add_item(
            user_id=user_admin.id,
            description="Receita estimada de setembro",
            amount=4389.00,
            transaction_type="income",
            category="Saldo",
            reference_month=MES,
            status="paid",
            transaction_date=datetime(2026, 9, 1),
            notes="Estimativa para fechar o mês com o saldo atual",
        )

        for desc, valor, cat, subcat, dt in [
            ("Aluguel - Apartamento", 700.00, "Moradia",     "Aluguel",      datetime(2026, 9, 5)),
            ("Supermercado - Extra",  500.00, "Alimentação", "Supermercado", datetime(2026, 9, 3)),
            ("Luz - CPFL",            150.00, "Serviços",    "Energia",      datetime(2026, 9, 8)),
            ("Internet - Fibra",      105.00, "Serviços",    "Internet",     datetime(2026, 9, 5)),
        ]:
            finance_service.add_item(
                user_id=user_admin.id,
                description=desc,
                amount=valor,
                transaction_type="expense",
                category=cat,
                subcategory=subcat,
                reference_month=MES,
                status="paid",
                transaction_date=dt,
                is_recurring=True,
                recurring_period="monthly",
            )

        summary = finance_service.get_summary(user_admin.id, reference_month=MES)

        logging.info("=" * 60)
        logging.info("✅ Banco populado com sucesso!")
        logging.info(f"📅 {MES} (vigente, aberto)")
        logging.info(f"   Receita: R$ {summary['total_income']:.2f}")
        logging.info(f"   Despesas: R$ {summary['total_expenses']:.2f}")
        logging.info(f"   Saldo: R$ {summary['total_balance']:.2f}")
        logging.info("👤 Usuários criados:")
        logging.info("   - leonan    / leonan2knet  (admin) — Jarvis")
        logging.info("   - thaiane   / 0302         (comum) — Tainá")
        logging.info("=" * 60)

    except Exception as e:
        logging.error(f"❌ Erro ao popular banco: {e}")
        session.rollback()
        raise
    finally:
        session.close()