function formatAmount(s) {  
  s += "";
  var num = s.replace(/,/g,'');
  if(!/^(\+|-)?\d+(\.\d+)?$/.test(num)){return 0;}  

  num = (num * 1).toFixed(2);
  var re = new RegExp().compile("(\\d)(\\d{3})(,|\\.|$)");  
  while(re.test(num))  
    num = num.replace(re,"$1,$2$3");
  return num; 
}

function curSymbol(cur) {
    if (cur == 'EUR')
        return '&euro;';
    return cur;
}

var message_catalog = {
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
    'Address': 'Addresse',
    'Billing': 'De facturation',
    'Shipping': 'De livraison',
    'Both': 'Both',
    'City': 'Ville',
    'Postal code': 'Code postal',
    'Country': 'Pays',
    'Description': 'Intitulé',

    'PENDING': "En attendant",
    'AWAITING_PAYMENT': 'En attente de paiement',
    'AWAITING_SHIPPING': "En attente d'expédition",
    'COMPLATED': "Expédiée",
};
function _trans(label) {
    var translated = message_catalog[label];
    if (translated == undefined)
        translated = label;
    return translated
}
