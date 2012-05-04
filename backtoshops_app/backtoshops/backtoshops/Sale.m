//
//  Sale.m
//  backtoshops
//
//  Created by Ding Nicholas on 2/15/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "Sale.h"
#import "Shop.h"

@implementation Sale

@synthesize identifier;
@synthesize name, description, imageURL, currency, price;
@synthesize discountType, discountValue;
@synthesize shops;

- (void)dealloc
{
    [identifier release];
    [name release];
    [description release];
    [imageURL release];
    [currency release];
    [price release];
    [discountType release];
    [discountValue release];
    [shops release];
    [super dealloc];
}

- (NSString *)discountPrice
{
    float discountPrice = [self.price floatValue] * (1 - [self.discountValue floatValue] / 100.0f);
    return [NSString stringWithFormat:@"%.0f", discountPrice];
}

- (NSString *)discountRatio
{
    return self.discountValue;
}

- (NSString *)toJSON
{
    NSMutableString *jsonText = [[[NSMutableString alloc] init] autorelease];
    [jsonText appendString:[NSString stringWithFormat:@"{'name': '%@', 'description': '%@', 'imageURL': '%@', 'currency': '%@', 'price': '%@', 'discountPrice': '%@', 'discountRatio': '%@'",
                            self.name, self.description, self.imageURL, self.currency, self.price, [self discountPrice], self.discountValue]];
    if (self.shops) {
        NSMutableArray *textArray = [NSMutableArray array];
        for (Shop *shop in self.shops) {
            [textArray addObject:[shop toJSON]];
        }
        [jsonText appendFormat:@", 'shops': [%@]", [textArray componentsJoinedByString:@","]];
    }
    
    [jsonText appendString:@"}"];
    
    return [jsonText copy];
}

+ (id)saleFromXML:(GDataXMLElement *)el
{
    Sale *saleObj = [[[Sale alloc] init] autorelease];
    saleObj.identifier = [[el attributeForName:@"id"] stringValue];
    saleObj.name = [[[el elementsForName:@"name"] lastObject] stringValue];
    saleObj.description = [[[el elementsForName:@"desc"] lastObject] stringValue];
    saleObj.imageURL = [[[el elementsForName:@"img"] lastObject] stringValue];
    saleObj.price = [[[el elementsForName:@"price"] lastObject] stringValue];
    saleObj.currency = [[[[el elementsForName:@"price"] lastObject] attributeForName:@"currency"] stringValue];
    saleObj.discountType = [[[[el elementsForName:@"discount"] lastObject] attributeForName:@"type"] stringValue];
    saleObj.discountValue = [[[el elementsForName:@"discount"] lastObject] stringValue];
    
    return saleObj;
}

- (id)initWithCoder:(NSCoder *)aDecoder
{
    self = [super init];
    if (self) {
        self.identifier = [aDecoder decodeObjectForKey:@"identifier"];
        self.name = [aDecoder decodeObjectForKey:@"name"];
        self.description = [aDecoder decodeObjectForKey:@"description"];
        self.imageURL = [aDecoder decodeObjectForKey:@"imageURL"];
        self.currency = [aDecoder decodeObjectForKey:@"currency"];
        self.price = [aDecoder decodeObjectForKey:@"price"];
        self.discountType = [aDecoder decodeObjectForKey:@"discountType"];
        self.discountValue = [aDecoder decodeObjectForKey:@"discountValue"];
        self.shops = [aDecoder decodeObjectForKey:@"shops"];
    }
    return self;
}

- (void)encodeWithCoder:(NSCoder *)aCoder
{    
    [aCoder encodeObject:self.identifier forKey:@"identifier"];
    [aCoder encodeObject:self.name forKey:@"name"];
    [aCoder encodeObject:self.description forKey:@"description"];
    [aCoder encodeObject:self.imageURL forKey:@"imageURL"];
    [aCoder encodeObject:self.currency forKey:@"currency"];
    [aCoder encodeObject:self.price forKey:@"price"];
    [aCoder encodeObject:self.discountType forKey:@"discountType"];
    [aCoder encodeObject:self.discountValue forKey:@"discountValue"];
    [aCoder encodeObject:self.shops forKey:@"shops"];
}

@end
