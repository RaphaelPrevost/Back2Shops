//
//  MainMenuController.m
//  B2SBarcodeScanner
//
//  Created by Ding Nicholas on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import "MainMenuController.h"
#import "AFJSONRequestOperation.h"

@implementation MainMenuController

@synthesize shopLabel;
@synthesize barReaderView;

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
    if (self) {
        // Custom initialization
    }
    return self;
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

    self.title = @"Barcode Scanner";
    self.barReaderView.readerDelegate = self;
}

- (void)viewDidAppear:(BOOL)animated
{
    // run the reader when the view is visible
    [self.barReaderView start];
}

- (void)viewWillDisappear:(BOOL)animated
{
    [self.barReaderView stop];
}

- (void)viewDidUnload
{
    [self setBarReaderView:nil];
    [self setShopLabel:nil];
    [super viewDidUnload];
    // Release any retained subviews of the main view.
    // e.g. self.myOutlet = nil;
}

- (BOOL)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation
{
    // Return YES for supported orientations
    return (interfaceOrientation == UIInterfaceOrientationPortrait);
}

- (void)dealloc {
    [barReaderView release];
    [shopLabel release];
    [super dealloc];
}

- (void)presentActionSheet:(NSString *)code
{
    UIActionSheet *actionSheet = [[UIActionSheet alloc] initWithTitle:[@"Barcode " stringByAppendingString:code]
                                                             delegate:self 
                                                    cancelButtonTitle:@"Cancel" 
                                               destructiveButtonTitle:nil 
                                                    otherButtonTitles:@"Set as Shop ID", @"Add Product", @"Remove Product", @"Custom Return", nil];
    [actionSheet showInView:self.view];
    [actionSheet release];
}

- (void)requestWithType:(NSInteger)actionType barcode:code
{

    NSURL *url;
    
    if (actionType == ActionTypeAdd) {
        url = [NSURL URLWithString:[API_HOST stringByAppendingString:@""]];
    } else if (actionType == ActionTypeRemove) {
        url = [NSURL URLWithString:[API_HOST stringByAppendingString:@""]];
    } else {
        url = [NSURL URLWithString:[API_HOST stringByAppendingString:@""]];
    }
    
    NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:url];
    AFJSONRequestOperation *operation = [AFJSONRequestOperation JSONRequestOperationWithRequest:request success:^(NSURLRequest *request, NSHTTPURLResponse *response, id JSON) {
        
    } failure:^(NSURLRequest *request, NSHTTPURLResponse *response, NSError *error, id JSON) {
        
    }];
    
    NSOperationQueue *queue = [[[NSOperationQueue alloc] init] autorelease];
    [queue addOperation:operation];
}

# pragma mark - ZBarReaderViewDelegate

- (void) readerView: (ZBarReaderView*) readerView
     didReadSymbols: (ZBarSymbolSet*) symbols
          fromImage: (UIImage*) image
{
    for (ZBarSymbol *symbol in symbols) {
        barcode = [symbol.data copy];
        [self presentActionSheet:barcode];
        break;
    }
}

#pragma mark - UIActionSheetDelegate

- (void)actionSheet:(UIActionSheet *)actionSheet clickedButtonAtIndex:(NSInteger)buttonIndex
{
    if (buttonIndex == 0) {
        self.shopLabel.text = barcode;
    } else {
        [self requestWithType:buttonIndex barcode:barcode];
    }
}

@end
