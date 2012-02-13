//
//  ShopInfoViewController.h
//  backtoshops
//
//  Created by Ding Nicholas on 2/5/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface ShopInfoViewController : UIViewController

@property (nonatomic, copy) NSString *shopID;
@property (retain, nonatomic) IBOutlet UIWebView *webView;

- (id)initWithShopID:(NSString *)shopID;

@end
