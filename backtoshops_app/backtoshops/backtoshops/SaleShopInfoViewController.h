//
//  SaleShopInfoViewController.h
//  backtoshops
//
//  Created by Ding Nicholas on 3/5/12.
//  Copyright (c) 2012 Nicholas Ding. All rights reserved.
//

#import <UIKit/UIKit.h>
#import "Sale.h"

@interface SaleShopInfoViewController : UIViewController <UIWebViewDelegate> {
    Sale *sale;
    NSMutableArray *saleList;
}

@property (nonatomic, copy) NSString *shopID;
@property (nonatomic, assign) NSInteger numberOfSales;
@property (retain, nonatomic) IBOutlet UIWebView *webView;

- (id)initWithSale:(Sale *)sale shopID:(NSString *)shopID;

- (void)loadSaleList;

@end
