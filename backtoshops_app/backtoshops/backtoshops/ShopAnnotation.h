//
//  ShopAnnotation.h
//  backtoshops
//
//  Created by Ding Nicholas on 2/8/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>
#import <MapKit/MapKit.h>

@interface ShopAnnotation : NSObject <MKAnnotation> {
    CLLocationCoordinate2D coordinate;
//    NSString *title;
//    NSString *subtitle;
}

@property (nonatomic, copy) NSString *title;
@property (nonatomic, copy) NSString *subtitle;

- (id)initWithCoordinate:(CLLocationCoordinate2D)coordinate title:(NSString *)title subtitle:(NSString *)subtitle;

@end
