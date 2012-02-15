//
//  Sale.m
//  backtoshops
//
//  Created by Ding Nicholas on 2/15/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "Sale.h"

@implementation Sale

@synthesize name, description, imageURL, price, discountPrice, discountRatio;

- (void)dealloc
{
    [name release];
    [description release];
    [imageURL release];
    [price release];
    [discountPrice release];
    [discountRatio release];
    [super dealloc];
}

- (NSString *)toJSON
{
    NSString *jsonText = [NSString stringWithFormat:@"{'name': '%@', 'description': '%@', 'imageURL': '%@', 'price': '%@', 'discountPrice': '%@', 'discountRatio': '%@'}",
                          self.name, self.description, self.imageURL, self.price, self.discountPrice, self.discountRatio];
    return jsonText;
}

@end
