//
//  ViewController.h
//  B2SBarcodeScanner
//
//  Created by Ding Nicholas on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface LoginViewController : UIViewController

@property (retain, nonatomic) IBOutlet UITextField *usernameField;
@property (retain, nonatomic) IBOutlet UITextField *passwordField;

- (IBAction)login:(id)sender;

@end
