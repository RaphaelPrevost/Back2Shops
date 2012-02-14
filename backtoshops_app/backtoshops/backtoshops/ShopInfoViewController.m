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

@implementation ShopInfoViewController

@synthesize shopID;
@synthesize webView;

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
    [shopID release];
    [webView release];
    [super dealloc];
}

#pragma mark - View lifecycle

- (void)viewDidLoad
{
    [super viewDidLoad];

    self.title = @"Le Shop";
    
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
    
    NSURLRequest *request = [NSURLRequest requestWithURL:[NSURL URLWithString:[@"http://sales.backtoshops.com/webservice/1.0/pub/shops/info/" stringByAppendingString:self.shopID]]];
    AFHTTPRequestOperation *operation = [[[AFHTTPRequestOperation alloc] initWithRequest:request] autorelease];
    [operation setCompletionBlockWithSuccess:^(AFHTTPRequestOperation *operation, id responseObject) {
        NSError *error;
        GDataXMLDocument *doc = [[GDataXMLDocument alloc] initWithData:responseObject options:0 error:&error];
        GDataXMLElement *root = doc.rootElement;
        
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
        [self.webView loadHTMLString:htmlTemplate baseURL:[NSURL fileURLWithPath:[[NSBundle mainBundle] pathForResource:@"ShopTemplate" ofType:@"html"]]];
        
        [doc release];
    } failure:^(AFHTTPRequestOperation *operation, NSError *error) {
        
    }];
    
    NSOperationQueue *queue = [[[NSOperationQueue alloc] init] autorelease];
    [queue addOperation:operation];
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

@end
