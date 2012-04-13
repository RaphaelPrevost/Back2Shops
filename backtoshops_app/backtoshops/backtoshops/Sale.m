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
@synthesize name, description, imageURL, currency, price, discountPrice, discountRatio;
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
    [discountPrice release];
    [discountRatio release];
    [discountType release];
    [discountValue release];
    [shops release];
    [super dealloc];
}

- (NSString *)toJSON
{
    NSMutableString *jsonText = [[[NSMutableString alloc] init] autorelease];
    [jsonText appendString:[NSString stringWithFormat:@"{'name': '%@', 'description': '%@', 'imageURL': '%@', 'currency': '%@', 'price': '%@', 'discountPrice': '%@', 'discountRatio': '%@'",
                            self.name, self.description, self.imageURL, self.currency, self.price, self.discountPrice, self.discountRatio]];
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
        self.discountRatio = [aDecoder decodeObjectForKey:@"discountRatio"];
        self.discountPrice = [aDecoder decodeObjectForKey:@"discountPrice"];
        self.discountType = [aDecoder decodeObjectForKey:@"discountType"];
        self.discountValue = [aDecoder decodeObjectForKey:@"discountValue"];
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
    [aCoder encodeObject:self.discountRatio forKey:@"discountRatio"];
    [aCoder encodeObject:self.discountPrice forKey:@"discountPrice"];
    [aCoder encodeObject:self.discountType forKey:@"discountType"];
    [aCoder encodeObject:self.discountValue forKey:@"discountValue"];
}

@end
