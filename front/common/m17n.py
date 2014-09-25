# -*- coding: utf-8 -*-
import settings
import logging

##
## message catalog to translate message
##
MESSAGE_CATALOG = {
    'en': {
        ## for django dollar
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

        ##
        'ORDER': 'Order',
        'CONTACT_CUSTOMER_SERVICE': 'Please contact customer service.',
        'NO_INVOICES': 'No invoices currently',

        'PENDING': "Waiting for confirmation",
        'AWAITING_PAYMENT': "Awaiting payment",
        'AWAITING_SHIPPING': "Awaiting shipment",
        'COMPLETED': "Shipped",

        'OFF_SCHEDULE_BY': 'Off schedule by : %(date)s',
        'SHIPPED_AT': 'Shipped at : %(date)s',

        'NEW_USER_EMAIL_SUBJECT': "Your account was created %(brand)s",
        'ORDER_EMAIL_SUBJECT': "Confirmation of your order",

        'RESET_PWD_EMAIL_SEND': "The reset password email has been sent to %(email)s",

        # error message
        'INTERNAL_SERVER_ERROR': "Sorry, our server met problems. Please try later.",
        'SERVER_ERR': 'Server error.',
        'DB_ERR': 'Server error.',
        'INVALID_REQUEST': 'Invalid request.',
        'ERR_EMAIL': 'Invalid email.',
        'ERR_PASSWORD': 'Invalid password.',
        'ERR_LOGIN': 'Invalid email or password.',
        'INVALID_FIRST_NAME': 'Invalid first name.',
        'INVALID_LAST_NAME': 'Invalid last name.',
        'INVALID_PHONE_NUMBER': 'Invalid phone number.',
        'INVALID_ADDRESS': 'Invalid address.',
        'INVALID_CITY': 'Invalid city.',
        'INVALID_POSTAL_CODE': 'Invalid postal code.',
        'FAILED_PLACE_ORDER': 'Failed to place your order.',
        'ERR_QUANTITY': 'Invalid quantity.',

        # user info form
        'Civility': 'Civility',
        'First name': 'First name',
        'Last name': 'Last name',
        'Title': 'Title',
        'Locale': 'Locale',
        'Gender': 'Gender',
        'Birthday': 'Birthday',
        'Email': 'Email',
        'Phone number': 'Phone number',
        'Calling code': 'Calling code',
        'Number': 'Number',
        'Address': 'Address',
        'Billing': 'Billing',
        'Shipping': 'Shipping',
        'Billing and shipping': 'Both',
        'Address type': 'Address type',
        'State or Province': 'State or Province',
        'City': 'City',
        'Postal code': 'Postal code',
        'Country': 'Country',
        'Description': 'Description',
        'Full name': 'Recipient',
    },

    'fr': {
        'PENDING': "En attente de confirmation",
        'AWAITING_PAYMENT': 'En attente de paiement',
        'AWAITING_SHIPPING': "En attente d'expédition",
        'COMPLETED': "Expédiée",

        'OFF_SCHEDULE_BY': 'Envoi prévu avant le : %(date)s',
        'SHIPPED_AT': 'Expédiée le : %(date)s',

        'NEW_USER_EMAIL_SUBJECT': "Votre compte %(brand)s à bien été créé",
        'ORDER_EMAIL_SUBJECT': "Confirmation de votre commande",

        # user info form
        'Civility': 'Civilité',
        'First name': 'Prénom',
        'Last name': 'Nom',
        'Title': 'Civilité',
        'Locale': 'Localisation',
        'Gender': 'Genre',
        'Birthday': 'Date de naissance',
        'Email': 'Email',
        'Phone number': 'Numéro de téléphone',
        'Calling code': 'Indicatif téléphonique',
        'Number': 'Numéro',
        'Address': 'Adresse',
        'Billing': 'De facturation',
        'Shipping': 'De livraison',
        'Billing and shipping': 'Les deux',
        'City': 'Ville',
        'Postal code': 'Code postal',
        'Country': 'Pays',
        'Description': 'Intitulé',
        'Full name': 'Destinataire',
    },
}

def create_m17n_func(lang):
    dct = MESSAGE_CATALOG.get(lang)
    if not dct:
        raise ValueError("%s: unknown lang." % lang)
    return dct.get

def trans_func(label, locale=settings.DEFAULT_LANG):
    if not label: return label

    try:
        text = create_m17n_func(locale)(label)
    except ValueError:
        text = None
    if not text and locale != 'en':
        logging.warning("Missing translation for %s (%s)" % (label, locale))
        text = create_m17n_func('en')(label)
    if not text:
        logging.error("Missing translation for %s (en)" % label)
        text = label
    return text

