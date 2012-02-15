//
//  SaleListViewController.h
//  backtoshops
//
//  Created by Ding Nicholas on 2/15/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface SaleListViewController : UIViewController <UIWebViewDelegate>

@property (nonatomic, copy) NSString *shopID;

@property (nonatomic, assign) NSInteger currentItemIndex;
@property (nonatomic, strong) NSArray *items;

@property (retain, nonatomic) IBOutlet UILabel *brandLabel;
@property (retain, nonatomic) IBOutlet UIWebView *webView;

@property (retain, nonatomic) IBOutlet UIButton *previousButton;
@property (retain, nonatomic) IBOutlet UIButton *nextButton;

- (id)initWithItems:(NSArray *)items;
- (id)initWithShopID:(NSString *)shopID;

- (IBAction)showPreviousSale;
- (IBAction)showNextSale;

@end

