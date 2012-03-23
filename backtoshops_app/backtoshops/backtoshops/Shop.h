//
//  Shop.h
//  backtoshops
//
//  Created by Ding Nicholas on 2/16/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>
#import <CoreLocation/CoreLocation.h>

@interface Shop : NSObject <NSCoding>

@property (nonatomic, copy) NSString *identifier;
@property (nonatomic, copy) NSString *name;
@property (nonatomic, copy) NSString *imageURL;
@property (nonatomic, copy) NSString *location;
@property (nonatomic, assign) CLLocationCoordinate2D coordinate;

- (NSString *)toJSON;

@end
