from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderDefinition:
    provider: str
    name: str
    store_slug: str | None
    channel: str
    capabilities: tuple[str, ...]
    note: str
    setup_url: str | None = None
    access_mode: str = "partnership"


PROVIDERS = (
    ProviderDefinition("mercadolivre", "Mercado Livre", "mercadolivre", "OAuth oficial", ("conta", "anuncios do vendedor"), "A API atual limita itens e buscas publicas para esta aplicacao.", "https://developers.mercadolivre.com.br/", "oauth"),
    ProviderDefinition("steam", "Steam", "steam", "Steam Web API", ("catalogo", "preco experimental"), "Catalogo oficial; preco via fonte publica nao documentada e controlada por feature flag.", "https://steamcommunity.com/dev/apikey", "api_key"),
    ProviderDefinition("amazon", "Amazon Brasil", "amazon-brasil", "Creators API", ("busca", "ofertas", "links afiliados"), "Exige conta Amazon Associates elegivel e credenciais da Creators API.", "https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction", "amazon"),
    ProviderDefinition("magalu", "Magazine Luiza", "magazine-luiza", "API de Sellers", ("catalogo do seller", "precos do seller"), "A API oficial e voltada ao seller autorizado, nao ao catalogo publico completo.", "https://developers.magalu.com/docs/", "magalu"),
    ProviderDefinition("awin", "Awin", None, "Rede de afiliados", ("programas", "promocoes"), "API de publisher pronta; o acesso aos anunciantes depende da aprovacao de cada programa.", "https://ui.awin.com/awin-api", "awin"),
    ProviderDefinition("casas-bahia", "Casas Bahia", "casas-bahia", "Afiliacao ou parceria", ("promocoes",), "Aguardando canal oficial aprovado para catalogo e precos.", access_mode="approval"),
    ProviderDefinition("centauro", "Centauro", "centauro", "Afiliacao ou parceria", ("promocoes",), "Aguardando canal oficial aprovado para catalogo e precos.", access_mode="approval"),
    ProviderDefinition("nike", "Nike", "nike", "Afiliacao ou parceria", ("promocoes",), "Aguardando aprovacao do anunciante ou integracao direta.", access_mode="approval"),
    ProviderDefinition("adidas", "Adidas", "adidas", "Afiliacao ou parceria", ("promocoes",), "Aguardando aprovacao do anunciante ou integracao direta.", access_mode="approval"),
    ProviderDefinition("shopee", "Shopee", "shopee", "Programa de afiliados", ("promocoes",), "Aguardando acesso oficial ao programa e ao contrato de dados.", access_mode="approval"),
    ProviderDefinition("havan", "Havan", "havan", "Parceria direta", ("promocoes",), "Nenhuma API publica oficial foi validada; requer feed ou parceria direta.", access_mode="partnership"),
)
