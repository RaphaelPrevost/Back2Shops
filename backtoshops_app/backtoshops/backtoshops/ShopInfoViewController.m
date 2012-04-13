//
//  ShopInfoViewController.m
//  backtoshops
//
//  Created by Ding Nicholas on 2/5/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "ShopInfoViewController.h"
#import "AFHTTPRequestOperation.h"
#import "GDataXMLNode.h"
#import "Shop.h"
#import "Sale.h"
#import "SaleListViewController.h"
#import "LocalCache.h"

@implementation ShopInfoViewController

@synthesize shopID;
@synthesize webView;
@synthesize numberOfSales;

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
    if (self) {
        // Custom initialization
    }
    return self;
}

- (id)initWithShopID:(NSString *)_shopID
{
    self = [super initWithNibName:@"ShopInfoViewController" bundle:nil];
    if (self) {
        self.shopID = _shopID;
        saleList = [[NSMutableArray alloc] init];
    }
    return self;
}

- (void)didReceiveMemoryWarning
{
    // Releases the view if it doesn't have a superview.
    [super didReceiveMemoryWarning];
    
    // Release any cached data, images, etc that aren't in use.
}

- (void)dealloc
{
    [saleList release];
    [shopID release];
    [webView release];
    [super dealloc];
}

#pragma mark - View lifecycle

- (void)viewDidLoad
{
    [super viewDidLoad];

    self.title = NSLocalizedString(@"Le Shop", nil);
    
    // Remove shadows of webview
    self.webView.opaque = NO;
    self.webView.backgroundColor = [UIColor clearColor];
    for (UIView* subView in [self.webView subviews]) {
        if ([subView isKindOfClass:[UIScrollView class]]) {
            for (UIView* shadowView in [subView subviews]) {
                if ([shadowView isKindOfClass:[UIImageView class]]) {
                    [shadowView setHidden:YES];
                }
            }
        }
    }
    
    // Create the queue
    NSOperationQueue *queue = [[[NSOperationQueue alloc] init] autorelease];
    queue.maxConcurrentOperationCount = 1;

    // Load Sales
    NSURLRequest *request = [NSURLRequest requestWithURL:[NSURL URLWithString:[@"http://sales.backtoshops.com/webservice/1.0/pub/sales/list?shop=" stringByAppendingString:self.shopID]]];
    AFHTTPRequestOperation *saleListOperation = [[[AFHTTPRequestOperation alloc] initWithRequest:request] autorelease];
    [saleListOperation setCompletionBlockWithSuccess:^(AFHTTPRequestOperation *operation, id responseObject) {
        NSError *error;
        GDataXMLDocument *doc = [[GDataXMLDocument alloc] initWithData:responseObject options:0 error:&error];
        self.numberOfSales = [[doc.rootElement elementsForName:@"sale"] count];
        
        for (GDataXMLElement *el in [doc.rootElement elementsForName:@"sale"]) {
            Sale *saleObj = [Sale saleFromXML:el];
            [saleList addObject:saleObj];
        }
        
        [doc release];
    } failure:^(AFHTTPRequestOperation *operation, NSError *error) {
        self.numberOfSales = 0;
    }];
    
    [queue addOperation:saleListOperation];
    
    // Load Shop
    NSDictionary *cachedShops = [[LocalCache sharedLocalCache] cachedDictionaryWithKey:@"ShopMap"];
    if ([cachedShops valueForKey:self.shopID]) {
        NSBlockOperation *shopInfoOeration = [NSBlockOperation blockOperationWithBlock:^{
            Shop *shop = (Shop *)[cachedShops valueForKey:self.shopID];
            NSString *path = [[NSBundle mainBundle] pathForResource:@"ShopTemplate" ofType:@"html"];
            NSString *htmlTemplate = [NSString stringWithContentsOfFile:path encoding:NSUTF8StringEncoding error:NULL];
            htmlTemplate = [htmlTemplate stringByReplacingOccurrencesOfString:@"$SHOP_NAME" withString:shop.name];
            htmlTemplate = [htmlTemplate stringByReplacingOccurrencesOfString:@"$ADDRESS" withString:shop.location];
            htmlTemplate = [htmlTemplate stringByReplacingOccurrencesOfString:@"$INFO" withString:shop.description];
            htmlTemplate = [htmlTemplate stringByReplacingOccurrencesOfString:@"$HOURS" withString:shop.hours];
            htmlTemplate = [htmlTemplate stringByReplacingOccurrencesOfString:@"$SHOP_OFFERS" withString:[NSString stringWithFormat:@"%d", self.numberOfSales]];
            [self.webView loadHTMLString:htmlTemplate baseURL:[NSURL fileURLWithPath:[[NSBundle mainBundle] pathForResource:@"ShopTemplate" ofType:@"html"]]];            
        }];
        
        [queue addOperation:shopInfoOeration];
    } else {
        request = [NSURLRequest requestWithURL:[NSURL URLWithString:[@"http://sales.backtoshops.com/webservice/1.0/pub/shops/info/" stringByAppendingString:self.shopID]]];
        AFHTTPRequestOperation *shopInfoOeration = [[[AFHTTPRequestOperation alloc] initWithRequest:request] autorelease];
        [shopInfoOeration setCompletionBlockWithSuccess:^(AFHTTPRequestOperation *operation, id responseObject) {
            NSError *error;
            GDataXMLDocument *doc = [[GDataXMLDocument alloc] initWithData:responseObject options:0 error:&error];
            GDataXMLElement *root = [[doc.rootElement elementsForName:@"shop"] lastObject];
            
            NSString *shopName = [[[root elementsForName:@"name"] lastObject] stringValue];
            NSString *shopAddress = [NSString stringWithFormat:@"%@<br/>%@ %@", [[[root elementsForName:@"addr"] lastObject] stringValue],
                                                                                [[[root elementsForName:@"zip"] lastObject] stringValue],
                                                                                [[[root elementsForName:@"city"] lastObject] stringValue]];
            NSString *info = [[[root elementsForName:@"desc"] lastObject] stringValue];
            NSString *hours = [[[root elementsForName:@"hours"] lastObject] stringValue];
            
            NSString *path = [[NSBundle mainBundle] pathForResource:@"ShopTemplate" ofType:@"html"];
            NSString *htmlTemplate = [NSString stringWithContentsOfFile:path encoding:NSUTF8StringEncoding error:NULL];
            htmlTemplate = [htmlTemplate stringByReplacingOccurrencesOfString:@"$SHOP_NAME" withString:shopName];
            htmlTemplate = [htmlTemplate stringByReplacingOccurrencesOfString:@"$ADDRESS" withString:shopAddress];
            htmlTemplate = [htmlTemplate stringByReplacingOccurrencesOfString:@"$INFO" withString:info];
            htmlTemplate = [htmlTemplate stringByReplacingOccurrencesOfString:@"$HOURS" withString:hours];
            htmlTemplate = [htmlTemplate stringByReplacingOccurrencesOfString:@"$SHOP_OFFERS" withString:[NSString stringWithFormat:@"%d", self.numberOfSales]];
            [self.webView loadHTMLString:htmlTemplate baseURL:[NSURL fileURLWithPath:[[NSBundle mainBundle] pathForResource:@"ShopTemplate" ofType:@"html"]]];
            
            [doc release];
        } failure:^(AFHTTPRequestOperation *operation, NSError *error) {
            
        }];
        
        [queue addOperation:shopInfoOeration];
    }
}

- (void)viewDidUnload
{
    [self setWebView:nil];
    [super viewDidUnload];
    // Release any retained subviews of the main view.
    // e.g. self.myOutlet = nil;
}

- (BOOL)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation
{
    // Return YES for supported orientations
    return (interfaceOrientation == UIInterfaceOrientationPortrait);
}

- (void)loadSaleList
{
    if ([saleList count] > 0) {
        SaleListViewController *controller = [[SaleListViewController alloc] initWithItems:saleList];
        [self.navigationController pushViewController:controller animated:YES];
        [controller release];
    }
}

#pragma mark - UIWebViewDelegate

- (BOOL)webView:(UIWebView *)webView shouldStartLoadWithRequest:(NSURLRequest *)request navigationType:(UIWebViewNavigationType)navigationType
{
    NSString *requestString = [[request URL] absoluteString];
    
//    NSLog(@"%@", requestString);
    
    if ([requestString isEqualToString:@"app://salelist"]) {
        [self loadSaleList];
        return NO;
    }
    
    return YES;
}

@end
