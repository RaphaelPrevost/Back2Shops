//
//  ShopAnnotation.m
//  backtoshops
//
//  Created by Ding Nicholas on 2/8/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "ShopAnnotation.h"

@implementation ShopAnnotation

@synthesize coordinate, title, subtitle;

- (id)initWithCoordinate:(CLLocationCoordinate2D)_coordinate title:(NSString *)_title subtitle:(NSString *)_subtitle
{
    self = [super init];
    if (self) {
        [self setCoordinate:_coordinate];
        self.title = _title;
        self.subtitle = _subtitle;
    }
    
    return self;
}

- (void)setCoordinate:(CLLocationCoordinate2D)newCoordinate
{
    coordinate = newCoordinate;
}

@end
