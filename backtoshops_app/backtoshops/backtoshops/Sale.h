//
//  Sale.h
//  backtoshops
//
//  Created by Ding Nicholas on 2/15/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface Sale : NSObject

@property (nonatomic, copy) NSString *name;
@property (nonatomic, copy) NSString *description;
@property (nonatomic, copy) NSString *imageURL;
@property (nonatomic, copy) NSString *price;
@property (nonatomic, copy) NSString *discountRatio;
@property (nonatomic, copy) NSString *discountPrice;

- (NSString *)toJSON;

@end
