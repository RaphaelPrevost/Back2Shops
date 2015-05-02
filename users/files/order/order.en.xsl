<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
    version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:date="http://exslt.org/dates-and-times"
    xmlns="http://www.w3.org/1999/xhtml">

    <xsl:output method="xml" indent="yes" encoding="UTF-8"/>

    <xsl:variable name="lang.invoiceDetails">Details</xsl:variable>
    <xsl:variable name="lang.refs">External reference</xsl:variable>
    <xsl:variable name="lang.description">Description</xsl:variable>
    <xsl:variable name="lang.quantity">Quantity</xsl:variable>
    <xsl:variable name="lang.unitPrice">Unit Price</xsl:variable>
    <xsl:variable name="lang.amount">Amount</xsl:variable>

    <xsl:template match="/order">
    <html>
        <head>
        </head>
        <body>
            <table border="1" width="400px">
                <tr>
                    <th><xsl:value-of select="$lang.refs" /></th>
                    <th><xsl:value-of select="$lang.description" /></th>
                    <th><xsl:value-of select="$lang.quantity" /></th>
                    <th><xsl:value-of select="$lang.unitPrice" /></th>
                    <th><xsl:value-of select="$lang.amount" /></th>
                </tr>
                <xsl:apply-templates select="item" />
            </table>
        </body>
    </html>
    </xsl:template>

    <xsl:template match="item">
        <tr class="row">
            <td class="refs">
                <xsl:value-of select="external_id" />
            </td>
            <td class="desc">
                <xsl:value-of select="name" />
                <xsl:if test="type and type !=''">
                    (<xsl:value-of select="type" />)
                </xsl:if>
            </td>
            <td class="qty">
                <xsl:value-of select="quantity" />
            </td>
            <td class="unitPrice">
                <xsl:value-of select="price" />
            </td>
            <td class="amount">
                <xsl:value-of select="price*quantity" />  <xsl:value-of select="currency" />
            </td>
        </tr>
    </xsl:template>

</xsl:stylesheet>
