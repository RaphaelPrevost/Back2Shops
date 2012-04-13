//
//  Sale.h
//  backtoshops
//
//  Created by Ding Nicholas on 2/15/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "GDataXMLNode.h"

@interface Sale : NSObject

@property (nonatomic, copy) NSString *identifier;
@property (nonatomic, copy) NSString *name;
@property (nonatomic, copy) NSString *description;
@property (nonatomic, copy) NSString *imageURL;
@property (nonatomic, copy) NSString *currency;
@property (nonatomic, copy) NSString *price;
@property (nonatomic, copy) NSString *discountRatio;
@property (nonatomic, copy) NSString *discountPrice;

// Newly added
@property (nonatomic, copy) NSString *discountType;
@property (nonatomic, copy) NSString *discountValue;

@property (nonatomic, strong) NSMutableArray *shops;

+ (id)saleFromXML:(GDataXMLElement *)el;

- (NSString *)toJSON;

@end
