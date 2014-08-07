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
