//
//  MainMenuController.m
//  B2SBarcodeScanner
//
//  Created by Ding Nicholas on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import "MainMenuController.h"
#import "LoginViewController.h"
#import "AFJSONRequestOperation.h"
#import "SVProgressHUD.h"

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
    
    self.navigationItem.rightBarButtonItem = [[[UIBarButtonItem alloc] initWithTitle:@"Logout" style:UIBarButtonItemStylePlain target:self action:@selector(logout)] autorelease];
    
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    if ([[defaults valueForKey:@"logged"] boolValue] == NO) {
        LoginViewController *loginViewController = [[LoginViewController alloc] initWithNibName:@"LoginViewController" bundle:nil];
        [self presentModalViewController:loginViewController animated:NO];
    }
    
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

- (void)logout
{
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    [defaults setBool:NO forKey:@"logged"];
    [defaults synchronize];
    
    LoginViewController *loginViewController = [[LoginViewController alloc] initWithNibName:@"LoginViewController" bundle:nil];
    [self presentModalViewController:loginViewController animated:YES];
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

- (void)requestWithType:(NSInteger)actionType barcode:(NSString *)code
{
    if ([self.shopLabel.text isEqualToString:@"(Scan to change)"]) {
        UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"Error" message:@"Please scan Shop ID first." delegate:nil cancelButtonTitle:@"Cancel" otherButtonTitles:nil];
        [alert show];
        [alert release];
        
        return;
    }
    
    [SVProgressHUD showInView:self.view];
    
    NSURL *url;
    
    if (actionType == ActionTypeAdd) {
        url = [NSURL URLWithString:[API_HOST stringByAppendingString:@"/webservice/1.0/private/stock/inc"]];
    } else if (actionType == ActionTypeRemove) {
        url = [NSURL URLWithString:[API_HOST stringByAppendingString:@"/webservice/1.0/private/stock/inc"]];
    } else {
        url = [NSURL URLWithString:[API_HOST stringByAppendingString:@"/webservice/1.0/private/stock/ret"]];
    }
    
    NSString *body = [NSString stringWithFormat:@"item=%@&shop=%@", code, self.shopLabel.text];
    NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:url];
    [request setHTTPBody:[body dataUsingEncoding:NSUTF8StringEncoding]];
    [request setHTTPMethod:@"POST"];
    
    AFJSONRequestOperation *operation = [AFJSONRequestOperation JSONRequestOperationWithRequest:request success:^(NSURLRequest *request, NSHTTPURLResponse *response, id JSON) {
        [SVProgressHUD dismiss];
        if ([[JSON valueForKey:@"success"] boolValue]) {
            UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"Notice" message:[NSString stringWithFormat:@"In Stock: %d", [[JSON valueForKey:@"total_stock"] intValue]] delegate:nil cancelButtonTitle:@"Cancel" otherButtonTitles:nil];
            [alert show];
            [alert release];
        } else {
            UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"Error" message:[JSON valueForKey:@"error"] delegate:nil cancelButtonTitle:@"Cancel" otherButtonTitles:nil];
            [alert show];
            [alert release];
        }
    } failure:^(NSURLRequest *request, NSHTTPURLResponse *response, NSError *error, id JSON) {
        NSLog(@"%@\n%@", error, JSON);
        if (response.statusCode == 403) {
            [SVProgressHUD dismissWithError:@"Login required."];
            [self performSelector:@selector(logout)];
        } else {
            [SVProgressHUD dismissWithError:@"Error occurred."];
        }
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
