//
//  Shop.m
//  backtoshops
//
//  Created by Ding Nicholas on 2/16/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "Shop.h"

@implementation Shop

@synthesize identifier, name, imageURL, location;
@synthesize coordinate;

- (void)dealloc
{
    [identifier release];
    [name release];
    [imageURL release];
    [location release];
    [super dealloc];
}

- (NSString *)toJSON
{
    NSString *jsonText = [NSString stringWithFormat:@"{'id': '%@', 'name': '%@', 'imageURL': '%@', 'location': \"%@\"}",
                          identifier, name, imageURL, location];
    return jsonText;
}

@end
