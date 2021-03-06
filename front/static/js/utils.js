function formatAmount(s, decimal_digits) {  
    s += "";
    var num = s.replace(/,/g,'');
    if(!/^(\+|-)?\d+(\.\d+)?$/.test(num)){return 0;}  

    if (decimal_digits == undefined)
        decimal_digits = 2

    num = (num * 1).toFixed(decimal_digits);
    //var re = new RegExp().compile("(\\d)(\\d{3})(,|\\.|$)");  
    //while(re && re.test(num))  
    //    num = num.replace(re,"$1,$2$3");

    if (decimal_digits > 2) { 
        count = decimal_digits - 2;
        while (count > 0) {
            if (num[num.length-1] == '0') {
                num = num.substring(0, num.length-1);
                count--;
                continue;
            } else {
                break;
            }
        }
    }
    return num; 
}

function curSymbol(cur) {
    if (cur == 'EUR')
        return '&euro;';
    return cur;
}

function redirectTo(url) {
    location = url;
}

function utf8_decode(utftext) {
    var string = "";
    var i = 0;
    var c = c1 = c2 = 0;

    while ( i < utftext.length ) {
        c = utftext.charCodeAt(i);

        if (c < 128) {
            string += String.fromCharCode(c);
            i++;
        } else if ((c > 191) && (c < 224)) {
            c2 = utftext.charCodeAt(i+1);
            string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
            i += 2;
        }
        else {
            c2 = utftext.charCodeAt(i+1);
            c3 = utftext.charCodeAt(i+2);
            string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
            i += 3;
        }
    }
    return string;
} 

function utf8_encode (string) {
    string = string.replace(/\r\n/g,"\n");
    var utftext = "";

    for (var n = 0; n < string.length; n++) {
        var c = string.charCodeAt(n);

        if (c < 128) {
            utftext += String.fromCharCode(c);
        } else if((c > 127) && (c < 2048)) {
            utftext += String.fromCharCode((c >> 6) | 192);
            utftext += String.fromCharCode((c & 63) | 128);
        } else {
            utftext += String.fromCharCode((c >> 12) | 224);
            utftext += String.fromCharCode(((c >> 6) & 63) | 128);
            utftext += String.fromCharCode((c & 63) | 128);
        }
    }
    return utftext;
}
