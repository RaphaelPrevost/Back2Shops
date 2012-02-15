//
//  SaleListViewController.m
//  backtoshops
//
//  Created by Ding Nicholas on 2/15/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "SaleListViewController.h"
#import "Sale.h"
#import "AFHTTPRequestOperation.h"
#import "GDataXMLNode.h"

@interface SaleListViewController (Private)

- (void)loadWebViewWithSale:(Sale *)item;
- (void)showNavigationArrows;

@end

@implementation SaleListViewController

@synthesize shopID;
@synthesize currentItemIndex;
@synthesize items;
@synthesize brandLabel;
@synthesize webView;
@synthesize previousButton;
@synthesize nextButton;

- (id)initWithItems:(NSArray *)_items
{
    self = [super initWithNibName:@"SaleListViewController" bundle:nil];
    if (self) {
        self.items = _items;
    }
    return self;    
}

- (id)initWithShopID:(NSString *)_shopID
{
    self = [super initWithNibName:@"SaleListViewController" bundle:nil];
    if (self) {
        self.shopID = _shopID;
    }
    return self;
}

//- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
//{
//    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
//    if (self) {
//        // Custom initialization
//    }
//    return self;
//}

- (void)dealloc
{
    [shopID release];
    [items release];
    [webView release];
    [brandLabel release];
    [previousButton release];
    [nextButton release];
    [super dealloc];
}

- (void)didReceiveMemoryWarning
{
    // Releases the view if it doesn't have a superview.
    [super didReceiveMemoryWarning];
    
    // Release any cached data, images, etc that aren't in use.
}

#pragma mark - View lifecycle

- (void)viewDidLoad
{
    [super viewDidLoad];

    self.title = @"Offre BTS";

    self.webView.opaque = NO;
    self.webView.backgroundColor = [UIColor clearColor];
    
    for (UIView* subView in [self.webView subviews]) {
        if ([subView isKindOfClass:[UIScrollView class]]) {
            for (UIView* shadowView in [subView subviews])
            {
                if ([shadowView isKindOfClass:[UIImageView class]]) {
                    [shadowView setHidden:YES];
                }
            }
        }
    }
    
    self.currentItemIndex = 0;
    
//    NSURLRequest *request = [NSURLRequest requestWithURL:[NSURL URLWithString:[@"http://sales.backtoshops.com/webservice/1.0/pub/sales/list?shop=" stringByAppendingString:self.shopID]]];
//    AFHTTPRequestOperation *operation = [[[AFHTTPRequestOperation alloc] initWithRequest:request] autorelease];
//    [operation setCompletionBlockWithSuccess:^(AFHTTPRequestOperation *operation, id responseObject) {
//        <#code#>
//    } failure:^(AFHTTPRequestOperation *operation, NSError *error) {
//        <#code#>
//    }];
//    
//    NSOperationQueue *queue = [[[NSOperationQueue alloc] init] autorelease];
//    [queue addOperation:operation];
    
    [self showNavigationArrows];
    [self loadWebViewWithSale:[self.items objectAtIndex:0]];
}

- (void)viewDidUnload
{
    [self setWebView:nil];
    [self setBrandLabel:nil];
    [self setPreviousButton:nil];
    [self setNextButton:nil];
    [super viewDidUnload];
    // Release any retained subviews of the main view.
    // e.g. self.myOutlet = nil;
}

- (BOOL)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation
{
    // Return YES for supported orientations
    return (interfaceOrientation == UIInterfaceOrientationPortrait);
}

- (void)loadWebViewWithSale:(Sale *)item
{
    self.brandLabel.text = item.name;
    
    NSString *path = [[NSBundle mainBundle] pathForResource:@"SaleInfoTemplate" ofType:@"html"];
    NSString *htmlTemplate = [NSString stringWithContentsOfFile:path encoding:NSUTF8StringEncoding error:NULL];
    htmlTemplate = [htmlTemplate stringByReplacingOccurrencesOfString:@"$JSON" withString:[item toJSON]];
    
    [self.webView stopLoading];
    [self.webView loadHTMLString:htmlTemplate baseURL:[NSURL fileURLWithPath:[[NSBundle mainBundle] pathForResource:@"SaleInfoTemplate" ofType:@"html"]]];
}

- (IBAction)showPreviousSale
{
    if (self.currentItemIndex - 1 >= 0) {
        self.currentItemIndex--;
        [self loadWebViewWithSale:[self.items objectAtIndex:self.currentItemIndex]];
    }
    
    [self showNavigationArrows];
}

- (IBAction)showNextSale
{
    if (self.currentItemIndex + 1 < [self.items count]) {
        self.currentItemIndex++;
        [self loadWebViewWithSale:[self.items objectAtIndex:self.currentItemIndex]];
    }
    
    [self showNavigationArrows];
}

- (void)showNavigationArrows
{
    self.previousButton.hidden = NO;
    self.nextButton.hidden = NO;
    
    if (self.currentItemIndex == 0) {
        self.previousButton.hidden = YES;
    }
    
    if (self.currentItemIndex == [self.items count] - 1) {
        self.nextButton.hidden = YES;
    }
}

#pragma mark - UIWebViewDelegate

- (void)webView:(UIWebView *)webView didFailLoadWithError:(NSError *)error
{
    NSLog(@"%@", error);
}

@end
