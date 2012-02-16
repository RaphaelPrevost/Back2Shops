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
@synthesize name, description, imageURL, price, discountPrice, discountRatio;
@synthesize shops;

- (void)dealloc
{
    [identifier release];
    [name release];
    [description release];
    [imageURL release];
    [price release];
    [discountPrice release];
    [discountRatio release];
    [shops release];
    [super dealloc];
}

- (NSString *)toJSON
{
    NSMutableString *jsonText = [[[NSMutableString alloc] init] autorelease];
    [jsonText appendString:[NSString stringWithFormat:@"{'name': '%@', 'description': '%@', 'imageURL': '%@', 'price': '%@', 'discountPrice': '%@', 'discountRatio': '%@'",
                            self.name, self.description, self.imageURL, self.price, self.discountPrice, self.discountRatio]];
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

@end
