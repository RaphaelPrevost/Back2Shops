//
//  SaleAnnotation.m
//  backtoshops
//
//  Created by Ding Nicholas on 5/4/12.
//  Copyright (c) 2012 Nicholas Ding. All rights reserved.
//

#import "SaleAnnotation.h"

@implementation SaleAnnotation

@synthesize saleID;
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
