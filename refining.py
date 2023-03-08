import requests
import streamlit as st
from operator import itemgetter


COLUMN_KEY_NAMES = {
    'item_id': 'Item',
    'city': 'Ciudad',
    'quality': '',
    'sell_price_min': 'Orden de Venta (Min)',
    'sell_price_min_date': '',
    'sell_price_max': 'Orden de Venta (Max)',
    'sell_price_max_date': '',
    'buy_price_min': 'Orden de Compra (Min)',
    'buy_price_min_date': '',
    'buy_price_max': 'Orden de Compra (Max)',
    'buy_price_max_date': ''
}


def get_key(key):
    return COLUMN_KEY_NAMES[key]


@st.cache_data()
def get_prices(items):
    url = "https://www.albion-online-data.com/api/v2/stats/prices/" + ",".join(items) + "?locations=Bridgewatch,Lymhurst,Martlock,Thetford,Fortsterling"
    json = requests.get(url).json()

    for row in json:
        for k, v in COLUMN_KEY_NAMES.items():
            if v == '':
                row.pop(k)
            else:
                row[v] = row.pop(k)

    return json


def get_product_price(product, prices):
    product_price_sell_order = max(filter(lambda p: p[get_key("item_id")] == product, prices), key=itemgetter(get_key("sell_price_min")))
    product_price_buy_order = max(filter(lambda p: p[get_key("item_id")] == product, prices), key=itemgetter(get_key("buy_price_max")))

    return product_price_sell_order, product_price_buy_order


def get_resource_price(resource, prices):
    return min(filter(lambda p: p[get_key("item_id")] == resource, prices), key=itemgetter(get_key("buy_price_max")))


def get_raw_resource(tier, item, enchantment):
    r = "T{tier}_{item}".format(tier=tier, item=item, enchantment=enchantment)

    if enchantment > 0:
        r = r + "_LEVEL{enchantment}@{enchantment}".format(enchantment=enchantment)

    return r


TIER_RAW_REQUIREMENTS = [0, 0, 1, 2, 2, 3, 4, 5, 5]
TIER_ITEM_VALUE = [0, 0, 0, 16, 32, 64, 128, 256, 512, 1024, 2048]

PREVIOUS_RAW_RESOURCE = {
    "PLANKS": "WOOD",
    "STONEBLOCK": "STONE",
    "METALBAR": "ORE",
    "LEATHER": "HIDE",
    "CLOTH": "FIBER"
}

RESOURCE_TRANSLATIONS = {
    'WOOD': 'Madera',
    'STONE': 'Piedra',
    'ORE': '',
    'HIDE': 'Piel',
    'FIBER': 'Fibra'
}

ITEM_TRANSLATIONS = {
    "PLANKS": "Tablas",
    "STONEBLOCK": "Bloques",
    "METALBAR": "Barras de Metal",
    "LEATHER": "Cuero",
    "CLOTH": "Tela"
}

st.set_page_config(
    page_title="Albion Refining Calculator",
    page_icon="🦄",
    layout="wide"
)

st.title("Calculadora de Refinamiento")

with st.form("calculator"):
    col11, col21, col31, col41 = st.columns(4)

    with col11:
        return_rate = st.number_input("Tasa de Retorno", value=36.7)
    with col21:
        return_rate_focus = st.number_input("Tasa de Retorno con Foco", value=53.9)
    with col31:
        fee = st.number_input("Precio de puesto de mercado", min_value=0, step=1)
    with col41:
        units = st.number_input("Unidades", min_value=1, step=1)

    col1, col2, col3 = st.columns(3)

    with col11:
        item = st.selectbox("Item", ITEM_TRANSLATIONS.keys(), format_func=lambda k: ITEM_TRANSLATIONS[k])
    with col21:
        tier = st.selectbox("Tier", [4, 5, 6, 7, 8])
    with col31:
        enchantment = st.selectbox("Encantamiento", [0, 1, 2, 3])

    with col11:
        st.form_submit_button("Calcular")
    with col21:
        with_focus = st.checkbox('con Foco')


def main():
    raw_resource = get_raw_resource(tier, PREVIOUS_RAW_RESOURCE[item], enchantment)
    crafted_resource = get_raw_resource(tier - 1, item, enchantment)
    product = get_raw_resource(tier, item, enchantment)

    item_value = TIER_ITEM_VALUE[tier + enchantment - 1]
    nutrition_cost = item_value * 0.1125
    fee_per_unit = (fee / 100) * nutrition_cost

    prices = get_prices([raw_resource, crafted_resource, product])
    with st.expander("Lista de Precios mas Recientes"):
        edited_prices = st.experimental_data_editor(prices, use_container_width=True)

    raw_resource_price = get_resource_price(raw_resource, edited_prices)
    crafted_resource_price = get_resource_price(crafted_resource, edited_prices)
    sell_order, buy_order = get_product_price(product, edited_prices)

    resource_cost = (raw_resource_price[get_key("buy_price_max")] * TIER_RAW_REQUIREMENTS[tier]) + crafted_resource_price[get_key("buy_price_max")]

    sell_order_profit_without_focus = ((sell_order[get_key("sell_price_min")] - resource_cost - fee_per_unit) + (resource_cost / 100 * return_rate)) * units
    sell_order_profit_with_focus = ((sell_order[get_key("sell_price_min")] - resource_cost - fee_per_unit) + (resource_cost / 100 * return_rate_focus)) * units
    buy_order_profit_without_focus = ((buy_order[get_key("buy_price_max")] - resource_cost - fee_per_unit) + (resource_cost / 100 * return_rate)) * units
    buy_order_profit_with_focus = ((buy_order[get_key("buy_price_max")] - resource_cost - fee_per_unit) + (resource_cost / 100 * return_rate_focus)) * units

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label=raw_resource_price[get_key("item_id")], value="{:,.0f}".format(raw_resource_price[get_key("buy_price_max")]))
        st.text(raw_resource_price[get_key("city")])

    with col2:
        st.metric(label=crafted_resource_price[get_key("item_id")], value="{:,.0f}".format(crafted_resource_price[get_key("buy_price_max")]))
        st.text(crafted_resource_price[get_key("city")])

    with col3:
        if with_focus:
            st.metric(label="Precio en Orden de Compra (con Foco)", value="{:,.0f}".format(buy_order[get_key("buy_price_max")]),
                      delta="{:,.0f}".format(buy_order_profit_with_focus))
            st.text(buy_order[get_key("city")])
        else:
            st.metric(label="Precio en Orden de Compra", value="{:,.0f}".format(buy_order[get_key("buy_price_max")]),
                      delta="{:,.0f}".format(buy_order_profit_without_focus))
            st.text(buy_order[get_key("city")])

    with col4:
        if with_focus:
            st.metric(label="Precio en Orden de Venta (Con Foco)", value="{:,.0f}".format(sell_order[get_key("sell_price_min")]),
                      delta="{:,.0f}".format(sell_order_profit_with_focus))
            st.text(sell_order[get_key("city")])
        else:
            st.metric(label="Precio en Orden de Venta", value="{:,.0f}".format(sell_order[get_key("sell_price_min")]),
                      delta="{:,.0f}".format(sell_order_profit_without_focus))
            st.text(sell_order[get_key("city")])

    footer = """
    <div>
        <style>
            .icon {
                text-align: center;
                margin-top: 50px;
                position: fixed;
                bottom: 20px;
                width: 100%;
            }
            .icon img {
                opacity: 0.5;
            }
            .icon img:hover {
                opacity: 1;
            }
            footer {
                display: none;
            }
        </style>
        <div class="icon">
            <a href="https://gats.ee" target="_blank"><img height="50" src="https://els-gats.s3.amazonaws.com/uploads/images/system/2022-08/els-01.png" /></a>
        </div>
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)


main()
