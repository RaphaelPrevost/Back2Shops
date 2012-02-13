//
//  SaleInfoViewController.h
//  backtoshops
//
//  Created by Ding Nicholas on 2/13/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface SaleInfoViewController : UIViewController

@property (nonatomic, copy) NSString *saleID;
@property (retain, nonatomic) IBOutlet UIWebView *webView;

- (id)initWithSaleID:(NSString *)saleID;

@end
