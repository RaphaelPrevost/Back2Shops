<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:date="http://exslt.org/dates-and-times"
  xmlns="http://www.w3.org/1999/xhtml">

  <xsl:import href="date.format-date.template.xsl" />

  <xsl:output method="xml" indent="yes" encoding="UTF-8"/>

  <xsl:variable name="lang.invoiceNumber">Facture &#8470;</xsl:variable>
  <xsl:variable name="lang.invoiceIssued">Éditée le</xsl:variable>
  <xsl:variable name="lang.dateFormat">d MMMM yyyy</xsl:variable>
  <xsl:variable name="lang.invoice">Facture</xsl:variable>
  <xsl:variable name="lang.invoiceDetails">Détail</xsl:variable>
  <xsl:variable name="lang.description">Description</xsl:variable>
  <xsl:variable name="lang.quantity">Quantité</xsl:variable>
  <xsl:variable name="lang.unitPrice">Prix Unitaire</xsl:variable>
  <xsl:variable name="lang.taxRate">Taxe</xsl:variable>
  <xsl:variable name="lang.amount">Montant</xsl:variable>
  <xsl:variable name="lang.discount">Réduction</xsl:variable>
  <xsl:variable name="lang.premium">Premium</xsl:variable> 
  <xsl:variable name="lang.subtotal">Sous-total</xsl:variable>
  <xsl:variable name="lang.shippingDesc">Service</xsl:variable>
  <xsl:variable name="lang.handling">Frais d'emballage</xsl:variable>
  <xsl:variable name="lang.shippingHandling">Frais de port et d'emballage</xsl:variable>
  <xsl:variable name="lang.taxAmount">Taxe</xsl:variable>
  <xsl:variable name="lang.total">Total</xsl:variable>
  <xsl:variable name="lang.businessNumber">SIRET</xsl:variable>
  <xsl:variable name="lang.taxNumber">Numéro de TVA intracommunautaire</xsl:variable>
  <xsl:variable name="lang.thanks"></xsl:variable>

  <xsl:template match="/invoices">
  <html>
      <head>
      </head>
      <body>
      <xsl:apply-templates select="invoice" />
      </body>
  </html>
  </xsl:template>

  <xsl:template match="invoice">
          <div id="header">
              <span id="invoiceNumber">
                  <xsl:value-of select="$lang.invoiceNumber" />
                  <span id="number">
                  <xsl:value-of select="@number" />
                  </span>
              </span>
              <span id="invoiceDate">
                  <xsl:value-of select="$lang.invoiceIssued" />
                  <span id="date">
                  <xsl:call-template name="date:format-date">
                      <xsl:with-param name="date-time" select="@date" />
                      <xsl:with-param name="pattern" select="$lang.dateFormat" />
                  </xsl:call-template>
                  </span>
              </span>
          </div>
          <xsl:apply-templates select="seller" />
          <xsl:apply-templates select="buyer" />
          <h1><xsl:value-of select="$lang.invoice" /></h1>
          <h2><xsl:value-of select="$lang.invoiceDetails" /></h2>
          <table border="1" width="400px">
              <tr>
                  <th><xsl:value-of select="$lang.description" /></th>
                  <th><xsl:value-of select="$lang.quantity" /></th>
                  <th><xsl:value-of select="$lang.unitPrice" /></th>
                  <th><xsl:value-of select="$lang.taxRate" /></th>
                  <th><xsl:value-of select="$lang.amount" /></th>
              </tr>
              <xsl:apply-templates select="item" />
          </table>
          <h2><xsl:value-of select="$lang.shippingHandling" /></h2>
          <table border="1" width="400px">
              <tr>
                  <th colspan="3"><xsl:value-of select="$lang.shippingDesc" /></th>
                  <th><xsl:value-of select="$lang.taxRate" /></th>
                  <th><xsl:value-of select="$lang.amount" /></th>
              </tr>
              <xsl:apply-templates select="shipping" />
          </table>
          <div id="invoiceNotes"></div>
          <div id="invoiceTotal">
              <label for="subtotal">
                 <xsl:value-of select="$lang.subtotal" />
              </label>
              <span id="subtotal"><xsl:value-of select="round(total/@gross*100) div 100.0" /></span>
              <label for="shippingHandling">
                 <xsl:value-of select="$lang.shippingHandling" />
              </label>
              <span id="shippingHandling">
                  <xsl:value-of select="round(shipping/postage*100) div 100.0 + round(shipping/handling*100) div 100.0" />
              </span>
              <label for="tax">
                  <xsl:value-of select="$lang.taxAmount" />
              </label>
              <span id="tax"><xsl:value-of select="round(total/@tax*100) div 100.0" /></span>
              <label for="total">
                  <xsl:value-of select="$lang.total" />
              </label>
              <span id="totalAmount"><xsl:value-of select="round(total*100) div 100.0" /></span>
          </div>
          <xsl:if test="seller/id">
          <div id="invoiceLegal">
              <xsl:if test="seller/id[@type='business']">
              <label for="idIncorporation">
                  <xsl:value-of select="$lang.businessNumber" />
              </label>
              <span id="idIncorporation">
                  <xsl:value-of select="seller/id[@type='business']" />
              </span>
              </xsl:if>
              <xsl:if test="seller/id[@type='tax']">
              <label for="idTax">
                  <xsl:value-of select="$lang.taxNumber" />
              </label>
              <span id="idTax">
                  <xsl:value-of select="seller/id[@type='tax']" />
              </span>
              </xsl:if>
          </div>
          </xsl:if>
          <div id="footer">
              <span id="thanks"><xsl:value-of select="$lang.thanks" /></span>
          </div>
  </xsl:template>

  <xsl:template match="seller">
          <div id="seller">
              <img id="sellerLogo" src="{img}" />
              <span id="sellerName"><xsl:value-of select="name" /></span>
              <xsl:apply-templates select="address" />
          </div>
  </xsl:template>

  <xsl:template match="address">
              <span class="addr"><xsl:value-of select="addr" /></span>
              <span class="zip"><xsl:value-of select="zip" /></span>
              <span class="city"><xsl:value-of select="city" /></span>
              <span class="province">
                  <xsl:value-of select="country/@province" />
              </span>
              <span class="country"><xsl:value-of select="country" /></span>
    </xsl:template>

    <xsl:template match="buyer">
        <div id="buyer">
            <span id="buyerName"><xsl:value-of select="name" /></span>
            <xsl:apply-templates select="address" />
        </div>
    </xsl:template>

    <xsl:template match="/invoices/invoice/item">
        <tr class="row">
            <td class="desc"><xsl:value-of select="desc" /></td>
            <td class="qty"><xsl:value-of select="qty" /></td>
            <xsl:if test="price/@original">
            <td class="unitPrice">
                <xsl:value-of select="price/@original" />
            </td>
            </xsl:if>
            <td class="taxRate" />
            <td class="amount">
                <xsl:if test="not(price/@original)">
                    <xsl:value-of select="price" />
                </xsl:if>
                <xsl:if test="price/@original">
                    <xsl:value-of select="price/@original" />
                </xsl:if>
            </td>
        </tr>
        <xsl:apply-templates select="detail" />
        <xsl:if test="price/@original">
        <tr class="discount row">
            <td colspan="3" class="desc">
                <xsl:value-of select="$lang.discount" />
            </td>
            <td class="taxRate" />
            <td class="amount">
                <xsl:value-of select="price - round(price/@original*100) div 100.0" />
            </td>
        </tr>
        </xsl:if>
        <xsl:if test="premium">
        <tr class="premium row">
            <td colspan="3" class="desc">
                <xsl:value-of select="$lang.premium" />
            </td>
            <td class="taxRate" />
            <td class="amount">
                <xsl:value-of select="round(premium*100) div 100.0" />
            </td>
        </tr>
        </xsl:if>
        <xsl:apply-templates select="tax" />
        <tr class="itemTotal row">
            <td colspan="4" class="desc">
                <xsl:value-of select="$lang.subtotal" />
            </td>
            <td class="subtotal"><xsl:value-of select="round(subtotal*100) div 100.0" /></td>
        </tr>
    </xsl:template>

    <xsl:template match="detail">
        <tr class="detail row">
            <td colspan="5">
                <ul class="itemDetail">
                <xsl:apply-templates select="subitem" />
                </ul>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="subitem">
                    <li class="subItem">
                        <span class="subQty"><xsl:value-of select="qty" /></span>
                        <span class="subDesc"><xsl:value-of select="desc" /></span>
                    </li>
    </xsl:template>

    <xsl:template match="tax">
        <tr class="tax row">
            <td colspan="3" class="desc"><xsl:value-of select="@name" /></td>
            <td class="taxRate">
                <xsl:value-of select="round(self::node() div @amount * 10000) div 100.0" /><xsl:text>%</xsl:text>
            </td>
            <td class="amount"><xsl:value-of select="round(@amount*100) div 100.0" /></td>
        </tr>
    </xsl:template>

    <xsl:template match="shipping">
        <tr class="shipping row">
            <td colspan="3" class="desc"><xsl:value-of select="desc" /></td>
            <td class="taxRate" />
            <td class="amount">
                <xsl:value-of select="postage" />
            </td>
        </tr>
        <xsl:if test="handling">
        <tr class="handling row">
            <td colspan="3" class="desc">
                <xsl:value-of select="$lang.handling" />
            </td>
            <td class="taxRate" />
            <td class="amount">
                <xsl:value-of select="handling" />
            </td>
        </tr>
        </xsl:if>
        <xsl:apply-templates select="tax" />
        <tr class="shippingTotal row">
            <td colspan="4" class="desc">
                <xsl:value-of select="$lang.shippingHandling" />
            </td>
            <td class="subtotal"><xsl:value-of select="subtotal" /></td>
        </tr>
    </xsl:template>

</xsl:stylesheet>
