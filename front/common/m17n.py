##
## message catalog to translate message
##

MESSAGE_CATALOG = {
    'en': {
        'TITLE': 'Dragon Dollar & Chinese Coins',
        'BUY': 'Buy',
        'LEARN': 'Learn',
        'COLLECT': 'Collect',
        'LIBRARY': 'Library',
        'YOUR_COIN_WORTH': 'What is your chinese coin worth ?',
        'DRAGON_DOLLARS': 'Dragon Dollars',
        'TERMS_CONDITIONS': 'Terms & Conditions',
        'COPYRIGHT': 'Copyright @ 2013-2014 Dragon Dollar Limited',
        'EMAIL': 'Email',
        'PASSWORD': 'Password',
        'VERIFY_PASSWORD': 'Verify Password',
        'REGISTER': 'Register',
        'LOGIN': 'Login',
        'CATALOG_REF': 'Catalog ref',
        'WEIGHT': 'Weight',
        'CONDITION': 'Condition',
        'CERT': 'Cert',
        'CHECK_CERTIFICATE': 'Check Certificate',
        'ADD_TO_WISHLIST': 'Add to Wishlist',
        'DRAGONDOLLAR_WARRANTY': 'DragonDollar Warranty',
        'DETAIL': 'Detail',
        'CHECKOUT': 'Checkout',
    },
}

def create_m17n_func(lang):
    dct = MESSAGE_CATALOG.get(lang)
    if not dct:
        raise ValueError("%s: unknown lang." % lang)
    return dct.get

