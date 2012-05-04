//
//  MainTabController.m
//  backtoshops
//
//  Created by Ding Nicholas on 2/2/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "MainTabController.h"
#import "HomeViewController.h"
#import "ShopViewController.h"
#import "LoginViewController.h"
#import "SearchViewController.h"
#import "OrderViewController.h"
#import "NearbySaleListViewController.h"
#import "LocalCache.h"
#import "AFHTTPRequestOperation.h"
#import "GDataXMLNode.h"
#import "Shop.h"
#import "Sale.h"

@interface MainTabController (Private)

- (void)loadCache;
- (void)deselectTab;
- (UIViewController *)createController:(NSString *)className;

@end

@implementation MainTabController

@synthesize viewControllers;
@synthesize currentController;
@synthesize contentView;
@synthesize tabbar;

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
    if (self) {
        self.viewControllers = [[NSMutableArray alloc] init];
    }
    return self;
}

#pragma mark - View lifecycle

- (void)viewDidLoad
{
    [super viewDidLoad];

    [self loadCache];
    
    // Trouver
    [self.viewControllers addObject:[self createController:@"SearchViewController"]];

    // Les Offres BTS
    [self.viewControllers addObject:[self createController:@"NearbySaleListViewController"]];
    
    // Les Shops
    [self.viewControllers addObject:[self createController:@"ShopViewController"]];
    
    // Mes achets
    [self.viewControllers addObject:[self createController:@"OrderViewController"]];
    
    [self click1st:nil];
}

- (void)viewDidUnload
{
    [super viewDidUnload];
    // Release any retained subviews of the main view.
    // e.g. self.myOutlet = nil;
}

- (BOOL)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation
{
    // Return YES for supported orientations
    return (interfaceOrientation == UIInterfaceOrientationPortrait);
}

- (void)setCurrentController:(UIViewController *)_currentController
{
    if (self.currentController) {
        [self.currentController.view removeFromSuperview];
    }
    
    [self.contentView addSubview:_currentController.view];
    
    [currentController release];
    currentController = [_currentController retain];
}

- (void)presentLoginViewController:(BOOL)animated
{
    LoginViewController *controller = [[LoginViewController alloc] initWithNibName:@"LoginViewController" bundle:nil];
    [self presentModalViewController:controller animated:animated];
    [controller release];
}

- (IBAction)click1st:(id)sender
{
    [self deselectTab];
    
    UIImageView *imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagFirst];
    imageView.image = [UIImage imageNamed:@"icons_01_on"];
    
    self.currentController = [self.viewControllers objectAtIndex:0];
}

- (IBAction)click2nd:(id)sender
{
    [self deselectTab];
    
    UIImageView *imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagSecond];
    imageView.image = [UIImage imageNamed:@"icons_02_on"];
    
    self.currentController = [self.viewControllers objectAtIndex:1];
}

- (IBAction)click3rd:(id)sender
{
    [self deselectTab];
    
    UIImageView *imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagThird];
    imageView.image = [UIImage imageNamed:@"icons_03_on"];
    
    self.currentController = [self.viewControllers objectAtIndex:2];
}

- (IBAction)click4th:(id)sender
{
    [self deselectTab];
    
    UIImageView *imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagFourth];
    imageView.image = [UIImage imageNamed:@"icons_04_on"];
    
    self.currentController = [self.viewControllers objectAtIndex:3];    
}

#pragma mark - Private

- (UIViewController *)createController:(NSString *)className
{
    UIViewController *controller = [[[NSClassFromString(className) alloc] initWithNibName:className bundle:nil] autorelease];
    UINavigationController *nav = [[[UINavigationController alloc] initWithRootViewController:controller] autorelease];
    nav.view.frame = CGRectMake(0, 0, 320, 415);
    
    return nav;
}

- (void)deselectTab
{
    UIImageView *imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagFirst];
    imageView.image = [UIImage imageNamed:@"icons_01_off"];

    imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagSecond];
    imageView.image = [UIImage imageNamed:@"icons_02_off"];
    
    imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagThird];
    imageView.image = [UIImage imageNamed:@"icons_03_off"];
    
    imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagFourth];
    imageView.image = [UIImage imageNamed:@"icons_04_off"];
}

- (void)loadCache
{
    // Load shop list from webservice
    NSURLRequest *request1 = [NSURLRequest requestWithURL:[NSURL URLWithString:@"http://sales.backtoshops.com/webservice/1.0/pub/shops/list"]];
    AFHTTPRequestOperation *operation1 = [[[AFHTTPRequestOperation alloc] initWithRequest:request1] autorelease];
    [operation1 setCompletionBlockWithSuccess:^(AFHTTPRequestOperation *operation, id responseObject) {
        NSMutableDictionary *shopMap = [NSMutableDictionary dictionary];
        NSError *error;
        GDataXMLDocument *doc = [[GDataXMLDocument alloc] initWithData:responseObject options:0 error:&error];
        for (GDataXMLElement *shop in [doc.rootElement elementsForName:@"shop"]) {
            Shop *shopObj = [Shop shopFromXML:shop];
            [shopMap setValue:shopObj forKey:shopObj.identifier];
        }
        
        [[LocalCache sharedLocalCache] storeDictionary:shopMap forKey:@"ShopMap"];
        [doc release];
    } failure:^(AFHTTPRequestOperation *operation, NSError *error) {
        
    }];
    
    NSURLRequest *request2 = [NSURLRequest requestWithURL:[NSURL URLWithString:@"http://sales.backtoshops.com/webservice/1.0/pub/sales/list"]];
    AFHTTPRequestOperation *operation2 = [[[AFHTTPRequestOperation alloc] initWithRequest:request2] autorelease];
    [operation2 setCompletionBlockWithSuccess:^(AFHTTPRequestOperation *operation, id responseObject) {
        NSMutableDictionary *saleMap = [NSMutableDictionary dictionary];
        NSError *error;
        GDataXMLDocument *doc = [[GDataXMLDocument alloc] initWithData:responseObject options:0 error:&error];
        for (GDataXMLElement *sale in [doc.rootElement elementsForName:@"sale"]) {
            Sale *saleObj = [Sale saleFromXML:sale];
            
            NSMutableArray *shops = [NSMutableArray array];
            for (GDataXMLElement *shop in [sale elementsForName:@"shop"]) {
                Shop *shopObj = [Shop shopFromXML:shop];
                [shops addObject:shopObj];
                saleObj.shops = shops;
            }
            
            [saleMap setValue:saleObj forKey:saleObj.identifier];
        }
        
        [[LocalCache sharedLocalCache] storeDictionary:saleMap forKey:@"SaleMap"];
        [doc release];
    } failure:^(AFHTTPRequestOperation *operation, NSError *error) {
        
    }];
    
    NSOperationQueue *queue = [[[NSOperationQueue alloc] init] autorelease];
    queue.maxConcurrentOperationCount = 2;
    [queue addOperation:operation1];
    [queue addOperation:operation2];
}

@end
